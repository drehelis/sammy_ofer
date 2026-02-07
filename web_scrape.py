#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import hashlib
import os
import re
from pathlib import Path
from random import choice
from types import SimpleNamespace

import numpy as np
import requests
import ua_generator
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image

import db
from google_calendar import GoogleCalendarManager
from logger import logger
from metadata import TEAMS_METADATA
from static_html_page import gen_static_page

load_dotenv()


def random_ua():
    return ua_generator.generate(device="desktop").headers.get()


class WebScrape:
    def __init__(self):
        self.url = "https://www.haifa-stadium.co.il/לוח_המשחקים_באצטדיון"
        self.soup = None

    @staticmethod
    def parse_date_string(date_str):
        date_formats = [
            ("%d/%m/%y %H:%M", False),    # 05/04/25 18:30
            ("%d/%m/%Y %H:%M", False),    # 05/04/2025 18:30
            ("%d.%m.%y %H:%M", False),    # 05.04.25 18:30
            ("%d.%m.%Y %H:%M", False),    # 05.04.2025 18:30
            ("%d-%m-%y %H:%M", False),    # 05-04-25 18:30
            ("%d-%m-%Y %H:%M", False),    # 05-04-2025 18:30
            ("%Y-%m-%d %H:%M", False),    # 2025-04-05 18:30
            ("%d/%m %H:%M", True),        # 05/04 18:30 - needs current year
        ]
        
        for fmt, needs_year in date_formats:
            try:
                dt = datetime.datetime.strptime(date_str, fmt)
                if needs_year:
                    dt = dt.replace(year=datetime.datetime.today().year)
                return dt
            except ValueError:
                continue
        return None

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

    def decorate_game_data(self, scraped):
        if isinstance(scraped, str):
            if not self.conn_err:
                gen_static_page({})
            return scraped

        arr_obj = []
        game_id = None

        for key, value in scraped.items():
            league, home_team, str_time, guest_team, *extra = value

            tidy_str_time = "".join(
                char for char in str_time if not char.isalpha()
            ).strip()

            if not tidy_str_time:  # skip entry if returns nothing (usually when there's bad input instead of date)
                logger.error(f"Skipping bad entry: {value}")
                continue

            scraped_date_time = self.parse_date_string(tidy_str_time)
            if not scraped_date_time:
                logger.error(f"No valid date format found for '{tidy_str_time}' in entry: {value}")
                continue

            GenerateTeamsPNG(home_team, guest_team).fetch_logo()

            game_id = hashlib.sha1(scraped_date_time.isoformat().encode()).hexdigest()

            game_time_delta = scraped_date_time - datetime.timedelta(hours=2)
            road_block_time = game_time_delta.time().strftime("%H:%M")
            custom_road_block_time = f"החל מ {road_block_time}"

            specs_word = extra[0] if len(extra) > 0 else "לא ידוע"
            sched_time = extra[1] if len(extra) > 1 else "09:00"
            specs_number = extra[2] if len(extra) > 2 else 0
            post_specs_number = extra[3] if len(extra) > 3 else 0
            poll = extra[4] if len(extra) > 4 else "off"
            notes = extra[5] if len(extra) > 5 else ""

            try:
                dbrecord = SimpleNamespace(**db.get_game_details(game_id))
                if extra:
                    dbrecord.specs_word = specs_word
                    dbrecord.sched_time = sched_time
                    dbrecord.specs_number = specs_number
                    dbrecord.post_specs_number = post_specs_number
                    dbrecord.poll = poll
                    dbrecord.notes = notes
                    dbrecord.specs_emoji = ""
                    dbrecord.custom_road_block_time = custom_road_block_time
            except TypeError:
                logger.info(f"Creating new record for game {game_id}")
                home_team_metadata = TEAMS_METADATA.get(
                    home_team, TEAMS_METADATA.get("Unavailable")
                )
                guest_team_metadata = TEAMS_METADATA.get(
                    guest_team, TEAMS_METADATA.get("Unavailable")
                )
                dbrecord = SimpleNamespace(
                    id=None,
                    game_id=game_id,
                    scraped_date_time=scraped_date_time.isoformat(),
                    league=league,
                    home_team=home_team,
                    home_team_en=home_team_metadata.get("name"),
                    home_team_url=home_team_metadata.get("url"),
                    game_hour=scraped_date_time.time().strftime("%H:%M"),
                    guest_team=guest_team,
                    guest_team_en=guest_team_metadata.get("name"),
                    guest_team_url=guest_team_metadata.get("url"),
                    game_time_delta=game_time_delta,
                    road_block_time=road_block_time,
                    specs_word=specs_word,
                    sched_time=sched_time,
                    specs_number=specs_number,
                    post_specs_number=post_specs_number,
                    poll=poll,
                    notes=notes,
                    specs_emoji="",
                    custom_road_block_time=custom_road_block_time,
                    created_at=datetime.datetime.now().isoformat(),
                )

            if int(dbrecord.specs_number) >= 28000:
                dbrecord.specs_emoji = "😱"

            if 1 <= int(dbrecord.specs_number) <= 6000:
                dbrecord.specs_emoji = "🤏"

            if dbrecord.specs_word == "ללא" or int(dbrecord.specs_number) <= 6000:
                dbrecord.custom_road_block_time = "אין"
            elif dbrecord.specs_word == "גדול מאוד":
                # default road block time is 2 hours before game start
                # for games with high attendance, set block road to 3 hours
                dbrecord.custom_road_block_time = f"החל מ {(datetime.datetime.strptime(getattr(dbrecord, 'road_block_time'), '%H:%M') - datetime.timedelta(hours=1)).strftime('%H:%M')}"

            arr_obj.append(dbrecord)

        db.store_scraped_games_in_db(arr_obj)

        gen_static_page(db.get_all_db_entries())

        return db.get_all_db_entries(), db.get_game_details(game_id)

    def create_calendar_event(self, games):
        if os.getenv("SKIP_CALENDAR"):
            logger.info("SKIP_CALENDAR is set, skipping calendar update")
            return

        upcoming, _ = games
        calendar_manager = GoogleCalendarManager()
        calendar_manager.authenticate()
        calendar_manager.create_events(upcoming)


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

        # Open images and convert all to RGB mode for consistency
        images = []
        for img_path in banner_list:
            img = Image.open(img_path)
            if img.mode != "RGB":
                white_bg = Image.new("RGB", img.size, (255, 255, 255))

                if img.mode == "RGBA":
                    white_bg.paste(img, (0, 0), img)
                    img = white_bg
                else:
                    img = img.convert("RGB")
            images.append(img)

        # pick the image which is the smallest, and resize the others to match it
        min_shape = sorted([(np.sum(i.size), i.size) for i in images])[0][1]

        # Resize all images to the same shape before stacking
        resized_images = [np.array(img.resize(min_shape)) for img in images]

        # Stack the images horizontally
        hstack = np.hstack(resized_images)

        images_combine = Image.fromarray(hstack)
        final_size = (770, 300)  # best found to fit telegram photo on mobile

        banner = images_combine.resize(final_size)
        banner.save(self.absolute_path / "banner.png")
