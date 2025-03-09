#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from random import choice
import datetime
from dateutil import parser
from pathlib import Path
from logger import logger
import hashlib
import os
import re
import requests


import numpy as np
from PIL import Image
from dotenv import load_dotenv

import db
from google_calendar import GoogleCalendarManager
from metadata import TEAMS_METADATA, DESKTOP_AGENTS
from static_html_page import gen_static_page

load_dotenv()


def random_ua():
    return {"User-Agent": choice(DESKTOP_AGENTS)}


class WebScrape:
    def __init__(self):
        self.url = "https://www.haifa-stadium.co.il/לוח_המשחקים_באצטדיון"
        self.time_delta = 2
        self.soup = None

    def scrape(self):
        try:
            response = requests.get(self.url, headers=random_ua(), timeout=60)
            response.raise_for_status()

            self.soup = BeautifulSoup(response.text, "html5lib")
        except requests.exceptions.HTTPError as err:
            logger.error(f"HTTPError: {err}")
            return f"<pre>{str(err)}</pre>"
        except requests.exceptions.ConnectionError as err:
            self.conn_err = True
            logger.error(f"ConnectionError: {err}")
            return f"<pre>{str(err)}</pre>"

        games_list = []
        class_regex = re.compile(
            "elementor-element elementor-element-[a-z0-9]{7} elementor-widget elementor-widget-text-editor"
        )

        if self.soup:
            result = self.soup.find_all("div", {"class": class_regex})
            for div in result:
                inner_divs = div.find_all("div")
                for inner_div in inner_divs:
                    paragraph = inner_div.find_all("p")
                    for p in paragraph:
                        text = p.get_text(separator=" ")  # treat </br> as space
                        text = text.strip(
                            "\t\r\n"
                        )  # strip tabs, newlines, spaces from the edges
                        games_list.append(text)

        if len(games_list) < 2:
            msg = "List returned empty, no games today?"
            logger.warning(msg)
            return f"<pre>{msg}</pre>"

        # https://stackoverflow.com/a/44104805/3399402
        games = {
            "game_{}".format(count): element
            for count, element in enumerate(zip(*[iter(games_list)] * 4), 1)
        }
        return games

    def decoratored_games(self, scraped):
        if isinstance(scraped, str):
            if not self.conn_err:
                gen_static_page({})
            return scraped

        deco_games_obj = {}
        for key, value in scraped.items():
            league, home_team, str_time, guest_team = value
            if len(list(filter(None, value))) != 4:  # skip if tuple is not whole
                continue

            tidy_str_time = "".join(
                char for char in str_time if not char.isalpha()
            ).strip()

            if not tidy_str_time:  # skip entry if returns nothing (usually when there's hebrew input instead of date)
                continue

            try:
                scraped_date_time = parser.parse(tidy_str_time, dayfirst=True)
            except parser.ParserError as err:
                logger.error(f"Failed to parse date in {value}': {err}")
                continue  # skip if date is in bad format

            GenerateTeamsPNG(home_team, guest_team).fetch_logo()

            game_id = hashlib.sha1(scraped_date_time.isoformat().encode()).hexdigest()
            home_team_en = TEAMS_METADATA.get(
                home_team, TEAMS_METADATA.get("Unavailable")
            ).get("name")
            home_team_url = TEAMS_METADATA.get(
                home_team, TEAMS_METADATA.get("Unavailable")
            ).get("url")
            guest_team_en = TEAMS_METADATA.get(
                guest_team, TEAMS_METADATA.get("Unavailable")
            ).get("name")
            guest_team_url = TEAMS_METADATA.get(
                guest_team, TEAMS_METADATA.get("Unavailable")
            ).get("url")

            game_hour = scraped_date_time.time().strftime("%H:%M")
            game_time_delta = scraped_date_time - datetime.timedelta(
                hours=self.time_delta
            )
            road_block_time = game_time_delta.time().strftime("%H:%M")

            specs_word, specs_number, post_specs_number, poll, notes = (
                db.get_game_details(game_id)
            )

            specs_emoji = ""
            custom_road_block_time = f"החל מ {road_block_time}"
            if int(specs_number) >= 28000:
                specs_emoji = "😱"
            if 1 <= int(specs_number) <= 6000:
                specs_emoji = "🤏"
            if specs_word == "ללא" or int(specs_number) <= 6000:
                custom_road_block_time = "אין"
            elif specs_word == "גדול מאוד":
                custom_road_block_time = f"החל מ {(datetime.datetime.strptime(road_block_time, '%H:%M') - datetime.timedelta(hours=1)).strftime('%H:%M')}"

            deco_games_obj.update(
                {
                    key: (
                        game_id,
                        scraped_date_time,
                        league,
                        home_team,
                        home_team_en,
                        home_team_url,
                        game_hour,
                        guest_team,
                        guest_team_en,
                        guest_team_url,
                        game_time_delta,
                        road_block_time,
                        specs_word,
                        specs_number,
                        post_specs_number,
                        poll,
                        notes,
                        #
                        specs_emoji,
                        custom_road_block_time,
                    )
                }
            )

        gen_static_page(deco_games_obj)

        db.store_scraped_games_in_db(deco_games_obj)

        return deco_games_obj

    def create_calendar_event(self, games):
        if os.getenv("SKIP_CALENDAR"):
            logger.info("SKIP_CALENDAR is set, skipping calendar update")
            return

        calendar_manager = GoogleCalendarManager()
        calendar_manager.authenticate()
        calendar_manager.create_events(games)


class GenerateTeamsPNG:
    def __init__(self, home_team, guest_team):
        self.home_team = TEAMS_METADATA.get(
            home_team, TEAMS_METADATA.get("Unavailable")
        )
        self.guest_team = TEAMS_METADATA.get(
            guest_team, TEAMS_METADATA.get("Unavailable")
        )
        self.absolute_path = Path(__file__).resolve().parent

        Path(self.absolute_path / "assets/teams").mkdir(parents=True, exist_ok=True)

    def fetch_logo(self):
        teams = (self.home_team, self.guest_team)

        for team in teams:
            fname = f"{team.get('name')}.png"
            logo_url = team.get("logo")

            full_path = self.absolute_path / Path("assets/teams") / fname
            if full_path.is_file():
                if full_path.stat().st_size != 0:
                    logger.debug(f"File '{full_path}' exists, fetching is skipped")
                    continue

            try:
                r = requests.get(logo_url, timeout=60)
                with open(full_path, "wb") as f:
                    logger.info(f"Writing new file '{full_path}'")
                    f.write(r.content)
            except requests.exceptions.MissingSchema:
                pass

    def banner(self):
        guest_team_fname = (
            self.absolute_path
            / Path("assets/teams")
            / f"{self.guest_team.get('name')}.png"
        )
        versus_image_fname = choice(
            list(Path(f"{self.absolute_path}/assets/versus").glob("**/*"))
        )
        home_team_fname = (
            self.absolute_path
            / Path("assets/teams")
            / f"{self.home_team.get('name')}.png"
        )

        banner_list = [guest_team_fname, versus_image_fname, home_team_fname]
        images = [Image.open(i) for i in banner_list]

        # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
        min_shape = sorted([(np.sum(i.size), i.size) for i in images])[0][1]
        hstack = np.hstack([i.resize(min_shape) for i in images])

        images_combine = Image.fromarray(hstack)
        final_size = (770, 300)  # best found to fit telegram photo on mobile

        banner = images_combine.resize(final_size)
        banner.save(self.absolute_path / "banner.png")
