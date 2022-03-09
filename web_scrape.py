#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from random import choice
from spectators import SPECTATORS
import datetime
import logging
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

DESKTOP_AGENTS = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0'
]

ERROR_MESSAGE = {
    'NO_GAMES_MSG': "List returned empty, no games today?",
    'CONNECT_ERROR': "Couldn't connect to {}{}"
}

def random_ua():
    return {'User-Agent': choice(DESKTOP_AGENTS)}

class WebScrape():
    def __init__(self):
        self.url = 'https://www.haifa-stadium.co.il/לוח_המשחקים_באצטדיון'
        self.time_delta = 2

    def scrape(self):
        try:
            response = requests.get(self.url, headers=random_ua())
            soup = BeautifulSoup(response.text, 'html5lib')
        except requests.exceptions.RequestException as err:
            logging.info(ERROR_MESSAGE['CONNECT_ERROR'].format(self.url, err.args[0].reason))
            return ERROR_MESSAGE['CONNECT_ERROR'].format(self.url, err.args[0].reason)

        games_list = []
        for div in soup.find_all("div", {"class": "elementor-text-editor elementor-clearfix"}):
            games_list.append(div.text)

        if len(games_list) < 2:
            logging.info(ERROR_MESSAGE['NO_GAMES_MSG'])
            return ERROR_MESSAGE['NO_GAMES_MSG']
        
        # https://stackoverflow.com/a/44104805/3399402
        games = {
            'game_{}'.format(count): element for count, element in enumerate(zip(*[iter(games_list)]*3), 1)
        }
        return games

    def decoratored_games(self, scraped):
        if isinstance(scraped, str):
            return scraped
        deco_games = {}
        for key, value in scraped.items():
            if not value[1]: # Skip entries with empty dates
                continue
            try:
              scraped_date_time = datetime.datetime.strptime(value[1], '%d-%m-%Y%H:%M')
            except ValueError as err:
              try:
                scraped_date_time = datetime.datetime.strptime(value[1], '%d-%m-%y%H:%M')
              except ValueError as err:
                try:
                  scraped_date_time = datetime.datetime.strptime(value[1], '%d/%m/%Y%H:%M')
                except ValueError as err:
                  try:
                    scraped_date_time = datetime.datetime.strptime(value[1], '%d/%m/%y%H:%M')
                  except ValueError as err:
                    try:
                      scraped_date_time = datetime.datetime.strptime(value[1], '%d/%m/%y')
                    except ValueError as err:
                      raise
            home_team = value[0]
            game_hour = scraped_date_time.time().strftime("%H:%M")
            guest_team = value[2]
            game_time_delta = scraped_date_time - datetime.timedelta(hours=self.time_delta)
            game_hour_delta = game_time_delta.time().strftime("%H:%M")
            specs_word = SPECTATORS.get((home_team, guest_team), {}).get('word', 'לא ידוע')
            specs_number = round(SPECTATORS.get((home_team, guest_team), {}).get('number', 0), -3)
            deco_games.update(
                {
                    key:(
                        scraped_date_time,
                        home_team,
                        game_hour,
                        guest_team,
                        game_time_delta,
                        game_hour_delta,
                        specs_word,
                        specs_number
                    )
                }
            )
        return deco_games