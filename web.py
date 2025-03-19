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
import web_scrape
from metadata import TEAMS_METADATA

app = Flask(__name__, template_folder="html_templates")
app.jinja_env.filters["babel_format_day_heb"] = jf.babel_format_day_heb


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
    ok = db.update_db_record(
        request.form["game_id"],
        request.form["specs_number"],
        request.form["post_specs_number"],
        request.form["specs_word"],
        request.form.get("poll", "off"),
        request.form["notes"],
        datetime.now().isoformat(),
    )
    if ok:
        return Markup("עידכון בוצע בהצלחה")


@app.route("/delete", methods=["POST"])
def delete():
    game_id = request.form.get("game_id")

    ok = db.delete_db_record(game_id)
    if ok:
        return Markup("הרשומה נמחקה בהצלחה")


@app.route("/add", methods=["POST"])
def add():
    ok = db.add_db_record(dict(request.form))
    if ok:
        return Markup("הרשומה התווספה בהצלחה")


@app.route("/assets/teams/<file_name>")
def get_image(file_name):
    try:
        return send_file(f"./assets/teams/{file_name}", mimetype="image/png")
    except FileNotFoundError:
        return app.response_class(status=404)


if __name__ == "__main__":
    app_access_logs = TransLogger(app)
    serve(app_access_logs, host="0.0.0.0", port=5000)
