#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import json
import shutil

from flask import Flask, render_template, request
from flask.helpers import send_file
from markupsafe import Markup
from waitress import serve
from paste.translogger import TransLogger


from spectators import SPECTATORS
import web_scrape
from jinja_filters import *

app = Flask(__name__, template_folder="html_templates")
app.jinja_env.filters["babel_format_day_heb"] = babel_format_day_heb


@app.route("/next", methods=["GET"])
def next_game():
    web = web_scrape.WebScrape()
    scrape = web.scrape()
    games = web.decoratored_games(scrape)

    if isinstance(games, str):
        return Markup(scrape)

    web.create_calendar_event(games)

    return render_template("next.html", mygames=games)


@app.route("/action", methods=["POST"])
def action():
    for _, val in request.form.items():
        return render_template("action.html", myval=json.loads(val))


@app.route("/update", methods=["POST"])
def update():
    home_team = request.form["home_team"]
    guest_team = request.form["guest_team"]
    d = {
        "number": int(request.form["specs_number"]),
        "word": request.form["specs_word"],
        "poll": request.form.get("poll", "off"),
        "notes": request.form.get("notes", ""),
    }

    # Backup the file before editing it
    spectators_file = "./spectators.py"
    backup_file = (
        f'{spectators_file}.backup-{datetime.now().strftime("%Y-%m-%d_%H%M%S")}'
    )
    shutil.copy(spectators_file, backup_file)

    key_exist = SPECTATORS.get((home_team, guest_team))
    if key_exist:
        SPECTATORS[home_team, guest_team].update(d)
        with open(spectators_file, "w", encoding="utf-8") as file:
            file.write(f"SPECTATORS = {SPECTATORS}")
        return Markup("השינויים נשמרו!")

    SPECTATORS[(home_team, guest_team)] = d
    with open(spectators_file, "w", encoding="utf-8") as file:
        file.write(f"SPECTATORS = {SPECTATORS}")
    return Markup("New entry saved!")


@app.route("/assets/teams/<file_name>")
def get_image(file_name):
    return send_file(f"./assets/teams/{file_name}", mimetype="image/png")


if __name__ == "__main__":
    app_access_logs = TransLogger(app)
    serve(app_access_logs, host="0.0.0.0", port=5000)
