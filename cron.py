#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import choice
import datetime
import logging
import os
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
    # Set today to datetime.date(YEAR, M, D) when debugging specific date
    today = datetime.date.today()
    for key, value in games.items():
        if today == value[0].date():
            logging.info("Yesh mishak!")
            yield value
    return False

def createMessage(*args):
    for item in args[0]:
        scraped_date_time = item[0]
        home_team = item[1]
        game_hour = item[2]
        guest_team = item[3]
        game_time_delta = item[4]
        road_block_time = item[5]
        specs_word = item[6]
        specs_number = item[7]

        custom_road_block_time = f"החל מ-{road_block_time}"
        if int(specs_number) >= 28000:
            custom_sepcs_number = f"({specs_number:,}) 😱"
        if specs_word == "ללא" or int(specs_number) < 5000:
            custom_road_block_time = "אין"
        elif specs_word == "גדול מאוד":
            custom_road_block_time = f"החל מ-{(datetime.datetime.strptime(road_block_time,'%H:%M') - datetime.timedelta(hours=1)).strftime('%H:%M')}"

        yield f"""
משחק ⚽ *היום* בשעה *{game_hour}*
משחקים: `{home_team} | {guest_team}`
צפי חסימת כבישים: *{custom_road_block_time}*
צפי אוהדים משוער: *{specs_word}* {custom_sepcs_number}

"""
emoji_hearts = ['💖','💞','💚','💜','💓','💙','💘','🤍','💗',
                '💕','💛','🧡','💝','🤎','❤️','❤️‍🔥','💟']
def random_emoji():
    return choice(emoji_hearts)

def send(msg, token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHANNEL_ID):
    bot = telegram.Bot(token=token)
    msgToSend = list(msg)
    msgToSend.append(f"_השירות מובא ב-{random_emoji()} לתושבי חיפה_")
    msgToSend.append(f"\n\n")
    msgToSend.append(f"[https://t.me/sammy_ofer_notification_channel](https://t.me/sammy_ofer_notification_channel)")
    bot.sendMessage(chat_id, text=''.join(msgToSend), parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True)
    logging.info('Telegram message sent!')

if __name__ == "__main__":
    web = web_scrape.WebScrape()
    scrape = web.scrape()
    games = web.decoratored_games(scrape)
    generatedData = checkForGamesToday(games)
    gameIsOnToday = list(generatedData)
    if gameIsOnToday:
        message = createMessage(gameIsOnToday)
        send(message)
    else:
        logging.info('There is only one thing we say to death - Not today!')
        sys.exit(1)
