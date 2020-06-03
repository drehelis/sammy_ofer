#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import logging
import sys
import telegram
import web_scrape

logging.basicConfig(level=logging.INFO)

if 'TELEGRAM_CHANNEL_ID' not in os.environ or 'TELEGRAM_TOKEN' not in os.environ:
    logging.info('Both \'TELEGRAM_CHANNEL_ID\' and \'TELEGRAM_TOKEN\' env. variables must be set.')
    sys.exit(1)
    
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

def checkForGamesToday(games):
    today = datetime.date.today()
    for key, value in games.items():
        if today == value[0].date():
            logging.info("Yesh mishak!")
            return value
    return False

def createMessage(*args):
    m = args[0]
    scraped_date_time = m[0]
    home_team = m[1]
    game_hour = m[2]
    guest_team = m[3]
    game_time_delta = m[4]
    game_hour_delta = m[5]
    specs_word = m[6]
    sepcs_number = m[7]
    return f"""
משחק ⚽ *היום* בשעה *{game_hour}*
משחקים: `{home_team} | {guest_team}`
צפי חסימת כבישים: החל מ-*{game_hour_delta}*
צפי אוהדים משוער: *{specs_word}* ({sepcs_number:,})

_השירות מובא ב-❤️ לתושבי חיפה_
    """

def send(msg, token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHANNEL_ID):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)
    logging.info('Telegram message sent!')

if __name__ == "__main__":
    web = web_scrape.WebScrape()
    scrape = web.scrape()
    games = web.decoratored_games(scrape)

    gameIsOnToday = checkForGamesToday(games)
    if gameIsOnToday:
        message = createMessage(gameIsOnToday)
        send(message)
    else:
        logging.info('There is only one thing we say to death - Not today!')
        sys.exit(1)
