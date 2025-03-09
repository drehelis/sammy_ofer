#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import json

from flask import Flask, render_template, request
from flask.helpers import send_file
from markupsafe import Markup
from waitress import serve
from paste.translogger import TransLogger

import web_scrape
import jinja_filters as jf
import db


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
        return render_template("action.html", myval=json.loads(val))


@app.route("/update", methods=["POST"])
def update():
    ok = db.update_db_record(
        request.form["game_id"],
        request.form["specs_number"],
        request.form["post_specs_number"],
        request.form["specs_word"],
        request.form.get("poll", "off"),
        request.form["notes"],
        datetime.now().isoformat()
    )
    if ok:
        return Markup("עידכון בוצע בהצלחה")


@app.route("/delete", methods=["POST"])
def delete():
    game_id = request.form.get("game_id")

    ok = db.delete_db_record(game_id)
    if ok:
        return Markup("הרשומה נמחקה בהצלחה")


@app.route("/assets/teams/<file_name>")
def get_image(file_name):
    return send_file(f"./assets/teams/{file_name}", mimetype="image/png")


if __name__ == "__main__":
    app_access_logs = TransLogger(app)
    serve(app_access_logs, host="0.0.0.0", port=5000)
