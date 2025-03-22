#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime

from flask import Flask, render_template, request
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

scheduler.scheduler_onstart()


@app.route("/next", methods=["GET"])
def next_game():
    web = web_scrape.WebScrape()
    scrape = web.scrape()
    games = web.decoratored_games(scrape)

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
    game_id = request.form.get("game_id")
    update_db = db.update_db_record(
        game_id,
        request.form["sched_time"],
        request.form["specs_number"],
        request.form["post_specs_number"],
        request.form["specs_word"],
        request.form.get("poll", "off"),
        request.form["notes"],
        datetime.now().isoformat(),
    )

    item = db.get_game_details(game_id)
    scheduler_date = datetime.fromisoformat(item["scraped_date_time"]).date()
    scheduler_time = datetime.strptime(request.form["sched_time"], "%H:%M").time()
    scheduler_dt = datetime.combine(scheduler_date, scheduler_time)
    update_sched = scheduler.scheduler_update(
        game_id,
        scheduler_dt,
    )

    if update_db and update_sched:
        return Markup("עידכון בוצע בהצלחה")


@app.route("/delete", methods=["POST"])
def delete():
    game_id = request.form.get("game_id")

    delete_db = db.delete_db_record(game_id)
    scheduler.scheduler_delete(game_id)

    if delete_db:
        return Markup("הרשומה נמחקה בהצלחה")


@app.route("/add", methods=["POST"])
def add():
    form = dict(request.form)

    add_db = db.add_db_record(form)
    add_scheduler = scheduler.scheduler_add(form)

    if add_db and add_scheduler:
        return Markup("הרשומה התווספה בהצלחה")


@app.route("/assets/teams/<file_name>")
def get_image(file_name):
    try:
        return send_file(f"./assets/teams/{file_name}", mimetype="image/png")
    except FileNotFoundError:
        return app.response_class(status=404)


if __name__ == "__main__":
    app_access_logs = TransLogger(app)
    serve(app_access_logs, host="0.0.0.0", port=5001)
