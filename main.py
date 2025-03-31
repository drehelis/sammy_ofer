#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask.helpers import send_file
from markupsafe import Markup
from paste.translogger import TransLogger
from waitress import serve

import db
import jinja_filters as jf
import scheduler
import web_scrape
from metadata import TEAMS_METADATA

app = Flask(__name__, template_folder="html_templates")
app.jinja_env.filters["babel_format_day_heb"] = jf.babel_format_day_heb
web = web_scrape.WebScrape()

if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler.scheduler_onstart()


def game_data_from_form(form):
    return {
        "stam": (
            form["league"],
            form["home_team"],
            f"{form['game_date']} {form['game_time']}",
            form["guest_team"],
            # below unpacked as extra
            form["specs_word"],
            form["sched_time"],
            form["specs_number"],
            form["post_specs_number"],
            form.get("poll", "off"),
            form["notes"],
        )
    }


@app.route("/next", methods=["GET"])
def next_game():
    scrape = web.scrape()
    games, _ = web.decorate_game_data(scrape)

    if isinstance(games, str):
        return Markup(scrape)

    web.create_calendar_event(games)

    all_games = db.get_all_db_entries()

    return render_template("next.html", mygames=all_games, datetime=datetime)


@app.route("/action", methods=["POST"])
def action():
    for _, val in request.form.items():
        return render_template(
            "action.html", myval=json.loads(val), teams_metadata=TEAMS_METADATA
        )


@app.route("/update", methods=["POST"])
def update():
    form = dict(request.form)
    data = game_data_from_form(form)
    _, updated_entry = web.decorate_game_data(data)

    scheduler_date = datetime.fromisoformat(updated_entry["scraped_date_time"]).date()
    scheduler_time = datetime.strptime(request.form["sched_time"], "%H:%M").time()
    scheduler_dt = datetime.combine(scheduler_date, scheduler_time)
    update_sched = scheduler.scheduler_update(
        updated_entry["game_id"],
        scheduler_dt,
    )

    if len(updated_entry) and update_sched:
        return Markup("עידכון בוצע בהצלחה")


@app.route("/delete", methods=["POST"])
def delete():
    game_id = request.form.get("game_id")

    delete_db = db.delete_db_record(game_id)
    scheduler.scheduler_delete(game_id)

    if delete_db:
        return Markup("הרשומה נמחקה בהצלחה")


@app.route("/send", methods=["POST"])
def send():
    try:
        scheduler.run_job()
        return jsonify({"status": "success", "message": "Job executed successfully"})
    except Exception as e:
        return jsonify(
            {"status": "error", "message": f"Error executing job: {str(e)}"}
        ), 500


@app.route("/add", methods=["POST"])
def add():
    form = dict(request.form)
    data = {
        "stam": (
            form["league"],
            form["home_team"],
            f"{form['game_date']} {form['game_time']}",
            form["guest_team"],
            # below unpacked as extra
            form["specs_word"],
            form["sched_time"],
            form["specs_number"],
            form["post_specs_number"],
            form.get("poll", "off"),
            form["notes"],
        )
    }

    _, added_entry = web.decorate_game_data(data)
    add_scheduler = scheduler.scheduler_add(added_entry)

    if len(added_entry) and add_scheduler:
        return Markup("הרשומה התווספה בהצלחה")


@app.route("/scheduler", methods=["GET"])
def scheduler_page():
    jobs = scheduler.list_jobs()

    return Markup(f"<pre>{'\n'.join(jobs)}</pre>")


@app.route("/assets/teams/<file_name>")
def get_image(file_name):
    try:
        return send_file(f"./assets/teams/{file_name}", mimetype="image/png")
    except FileNotFoundError:
        return app.response_class(status=404)


if __name__ == "__main__":
    app_access_logs = TransLogger(app)
    serve(app_access_logs, host="0.0.0.0", port=5001)
