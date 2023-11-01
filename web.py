#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from flask import Flask, render_template, request
from markupsafe import Markup
from spectators import SPECTATORS
import base64
import json
import locale
import shutil
import web_scrape

try:
    locale.setlocale(locale.LC_TIME, "he_IL")       # MacOS
except locale.Error:
    try:
        # apt-get install language-pack-he language-pack-he-base
        locale.setlocale(locale.LC_TIME, "he_IL.UTF-8") # Ubuntu
    except locale.Error:
        pass

def b64encode(s):
    return base64.b64encode(s.encode())

def b64decode(s):
    data = base64.b64decode(s)
    return data.decode()
   
app = Flask(__name__, template_folder='html_templates')
app.jinja_env.filters['b64encode'] = b64encode
app.jinja_env.filters['b64decode'] = b64decode

@app.route('/next', methods=['GET'])
def nextGame():
    web = web_scrape.WebScrape()
    scrape = web.scrape()
    games = web.decoratored_games(scrape)
    if isinstance(games, str):
        return Markup(scrape)

    return render_template('next.html', mygames=games)

@app.route('/action', methods=['POST'])
def action():
    for key, val in request.form.items():
        return render_template('action.html', myval=json.loads(val))

@app.route('/update', methods=['POST'])
def update():
    home_team = request.form['home_team']
    guest_team = request.form['guest_team']
    d = {
        "number": int(request.form['specs_number']),
        "word": request.form['specs_word'],
        "poll": request.form.get('poll', 'off'),
        "notes": request.form.get('notes', '')
    }
    
    # Backup the file before editing it
    spectators_file = './spectators.py'
    backup_file = f'{spectators_file}.backup-{datetime.now().strftime("%Y-%m-%d_%H%M%S")}'
    shutil.copy(spectators_file, backup_file)

    keyExist = SPECTATORS.get((home_team, guest_team))
    if keyExist:
        SPECTATORS[home_team, guest_team].update(d)
        with open(spectators_file, 'w') as file:
            file.write(f'SPECTATORS = {SPECTATORS}')
        return Markup("Saved!")
    else:
        SPECTATORS[(home_team, guest_team)] = d
        with open(spectators_file, 'w') as file:
            file.write(f'SPECTATORS = {SPECTATORS}')
        return Markup("New entry saved!")

if __name__ == "__main__":
    app.run
