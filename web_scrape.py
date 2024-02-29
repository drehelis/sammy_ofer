#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from random import choice
from spectators import SPECTATORS
import datetime
from dateutil import parser
import logging
import requests
import re

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

DESKTOP_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

def random_ua():
    return {"User-Agent": choice(DESKTOP_AGENTS)}


class WebScrape:
    def __init__(self):
        self.url = "https://www.haifa-stadium.co.il/לוח_המשחקים_באצטדיון"
        self.time_delta = 2
        self.soup = None

    def scrape(self):
        try:
            response = requests.get(self.url, headers=random_ua(), timeout=10)
            response.raise_for_status()

            self.soup = BeautifulSoup(response.text, "html5lib")
        except requests.exceptions.HTTPError as err:
            logging.error(f"HTTPError: {err}")
            return f"<pre>{str(err)}</pre>"
        except requests.exceptions.ConnectionError as err:
            logging.error(f"ConnectionError: {err}")
            return f"<pre>{str(err)}</pre>"

        games_list = []
        class_regex = re.compile("elementor-element elementor-element-[a-z0-9]{7} elementor-widget elementor-widget-text-editor")

        if self.soup:
            result = self.soup.find_all("div", {"class": class_regex})
            for div in result:
                inner_divs = div.find_all('div')
                for inner_div in inner_divs:
                    paragraph = inner_div.find_all('p')
                    for p in paragraph:
                        text = p.get_text(separator=" ")  # treat </br> as space
                        text = text.strip("\t\r\n")  # strip tabs, newlines, spaces from the edges
                        games_list.append(text)

        if len(games_list) < 2:
            return f"<pre>List returned empty, no games today? Scrape result: {result}</pre>"

        # https://stackoverflow.com/a/44104805/3399402
        games = {
            "game_{}".format(count): element
            for count, element in enumerate(zip(*[iter(games_list)] * 4), 1)
        }
        return games

    def decoratored_games(self, scraped):
        if isinstance(scraped, str):
            return scraped

        deco_games = {}
        for key, value in scraped.items():
            league, home_team, str_time, guest_team = value
            if len(list(filter(None, value))) != 4:  # skip if tuple is not whole
                continue

            tidy_str_time = "".join(
                char for char in str_time if not char.isalpha()
            ).strip()

            if (
                not tidy_str_time
            ):  # skip entry if returns nothing (usually when there's hebrew input instead of date)
                continue

            scraped_date_time = parser.parse(tidy_str_time, dayfirst=True)

            if (
                type(scraped_date_time) is not datetime.datetime
            ):  # skip if date is in bad format
                continue

            game_hour = scraped_date_time.time().strftime("%H:%M")
            game_time_delta = scraped_date_time - datetime.timedelta(
                hours=self.time_delta
            )
            game_hour_delta = game_time_delta.time().strftime("%H:%M")
            specs_word = SPECTATORS.get((home_team, guest_team), {}).get(
                "word", "לא ידוע"
            )
            specs_number = round(
                SPECTATORS.get((home_team, guest_team), {}).get("number", 0), -2
            )
            poll = SPECTATORS.get((home_team, guest_team), {}).get("poll")
            notes = SPECTATORS.get((home_team, guest_team), {}).get("notes", "")
            deco_games.update(
                {
                    key: (
                        scraped_date_time,
                        league,
                        home_team,
                        game_hour,
                        guest_team,
                        game_time_delta,
                        game_hour_delta,
                        specs_word,
                        specs_number,
                        poll,
                        notes,
                    )
                }
            )
        return deco_games
