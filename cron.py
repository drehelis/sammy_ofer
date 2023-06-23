#!/usr/bin/env python3

from random import choice
import asyncio
import datetime
import json
import logging
import os
import sys
import web_scrape

from dotenv import load_dotenv
from telegram import Bot, constants


logging.basicConfig(level=logging.INFO)
load_dotenv()

if 'TELEGRAM_CHANNEL_ID' not in os.environ or 'TELEGRAM_TOKEN' not in os.environ:
    logging.info(
        'Both \'TELEGRAM_CHANNEL_ID\' and \'TELEGRAM_TOKEN\' env. variables must be set.')
    sys.exit(1)

TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

emoji_hearts = ['💖', '💞', '💚', '💜', '💓', '💙', '💘', '🤍', '💗',
                '💕', '💛', '🧡', '💝', '🤎', '❤️', '❤️‍🔥', '💟', '❣️', '🖤']

poll_sentences = [
    'סקר: מי תנצח?',
    'סקר: מי תנצח במפגש בין שתי הקבוצות?',
    'סקר: מי תיקח הפעם?',
    'סקר: מי האחת שתנצח ותפתח ברגל ימין?',
    'סקר: מי הקבוצה הטובה יותר?',
    'סקר: אילו אוהדים יחגגו היום?'
]


def random_choice(rand):
    return choice(rand)


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
        scraped_date_time, league, home_team, game_hour, guest_team, game_time_delta, road_block_time, specs_word, specs_number, poll, notes = item

        custom_sepcs_number = f"({specs_number:,})"
        custom_road_block_time = f"החל מ-{road_block_time}"
        if int(specs_number) >= 28000:
            custom_sepcs_number = f"({specs_number:,}) 😱"
        if specs_word == "ללא" or int(specs_number) <= 6000:
            custom_road_block_time = "אין"
        elif specs_word == "גדול מאוד":
            custom_road_block_time = f"החל מ-{(datetime.datetime.strptime(road_block_time,'%H:%M') - datetime.timedelta(hours=1)).strftime('%H:%M')}"

        yield f"""
משחק ⚽ *היום* בשעה *{game_hour}*
*{league}*: `{home_team} | {guest_team}`
צפי חסימת כבישים: *{custom_road_block_time}*
צפי אוהדים משוער: *{specs_word}* {custom_sepcs_number}

""", (scraped_date_time, home_team, guest_team, poll, notes)


async def send(msg, token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHANNEL_ID):
    async with Bot(token) as bot:

        iterator = next(msg)

        msgToSend = list(iterator[:-1])
        iterated_data = iterator[-1]

        scraped_date_time = iterated_data[0]
        home_team = iterated_data[1]
        guest_team = iterated_data[2]
        poll = iterated_data[3]
        notes = iterated_data[4]

        if notes:
            msgToSend.append(f"📣: {notes}\n\n")

        msgToSend.append(
            f"_השירות מובא ב-{random_choice(emoji_hearts)} לתושבי חיפה_")
        msgToSend.append(f"\n\n")
        msgToSend.append(
            f"[https://t.me/sammy_ofer_notification_channel](https://t.me/sammy_ofer_notification_channel)")
        await bot.send_message(
            chat_id,
            text=''.join(msgToSend),
            parse_mode=constants.ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        logging.info('Telegram message sent!')

        if poll == 'on':
            await bot.sendPoll(
                chat_id,
                random_choice(poll_sentences),
                json.dumps([home_team, guest_team]),
                disable_notification=True,
                protect_content=True,
                close_date=datetime.datetime.timestamp(scraped_date_time)
            )
            logging.info('Telegram poll sent!')


if __name__ == "__main__":
    web = web_scrape.WebScrape()
    scrape = web.scrape()
    games = web.decoratored_games(scrape)
    generatedData = checkForGamesToday(games)
    gameIsOnToday = list(generatedData)
    if gameIsOnToday:
        message = createMessage(gameIsOnToday)
        asyncio.run(send(message))
    else:
        logging.info('There is only one thing we say to death - Not today!')
        sys.exit(1)
