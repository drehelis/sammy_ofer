#!/usr/bin/env python3

from random import choice
import asyncio
import datetime
from pathlib import Path
import json
import os
import sys
from dotenv import load_dotenv
from telegram import Bot, constants

from logger import logger
import web_scrape

from metadata import EMOJI_HEARTS, POLL_SENTENCES

load_dotenv()


if "TELEGRAM_CHANNEL_ID" not in os.environ or "TELEGRAM_TOKEN" not in os.environ:
    logger.info(
        "Both 'TELEGRAM_CHANNEL_ID' and 'TELEGRAM_TOKEN' env. variables must be set."
    )
    sys.exit(1)

TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

absolute_path = Path(__file__).resolve().parent


def random_choice(rand):
    return choice(rand)


def check_games_today(games):
    # Set today to datetime.date(YEAR, M, D) when debugging specific date
    today = datetime.date.today()
    for _, value in games.items():
        if today == value[0].date():
            logger.info("Yesh mishak!")
            yield value

    return False


def create_message(*args):
    # pylint: disable=unused-variable,too-many-locals
    for item in args[0]:
        (
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
            poll,
            notes,
            custom_sepcs_number,
            custom_road_block_time,
        ) = item

        yield f"""
משחק ⚽ *היום* בשעה *{game_hour}*
*{league}*: [{home_team}]({home_team_url}) \\|\\| [{guest_team}]({guest_team_url})
צפי חסימת כבישים: *{custom_road_block_time}*
צפי אוהדים משוער: *{specs_word}* {custom_sepcs_number}

""", (
            scraped_date_time,
            home_team,
            guest_team,
            poll,
            notes,
        )


async def send(msg, token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHANNEL_ID):
    async with Bot(token) as bot:

        iterator = next(msg)
        send_message = list(iterator[:-1])
        iterated_data = iterator[-1]

        scraped_date_time = iterated_data[0]
        home_team = iterated_data[1]
        guest_team = iterated_data[2]
        poll = iterated_data[3]
        notes = iterated_data[4]

        if notes:
            send_message.append(f"📣: {notes}\n\n")

        send_message.append(
            f"_השירות מובא ב {random_choice(EMOJI_HEARTS)} לתושבי חיפה_"
        )
        send_message.append("\n\n")
        send_message.append(
            "[https://t\\.me/sammy\\_ofer\\_notification\\_channel](https://t.me/sammy_ofer_notification_channel)"
        )

        web_scrape.GenerateTeamsPNG(home_team, guest_team).banner()

        await bot.send_photo(
            chat_id,
            photo=absolute_path / "banner.png",
            caption="".join(send_message),
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
        logger.info("Telegram message sent!")

        if poll == "on":
            await bot.sendPoll(
                chat_id,
                random_choice(POLL_SENTENCES),
                json.dumps([home_team, guest_team]),
                disable_notification=True,
                protect_content=True,
                close_date=datetime.datetime.timestamp(scraped_date_time),
            )
            logger.info("Telegram poll sent!")


if __name__ == "__main__":
    web = web_scrape.WebScrape()
    scrape = web.scrape()
    scraped_games = web.decoratored_games(scrape)
    generated_data = check_games_today(scraped_games)
    detected_games_today = list(generated_data)
    message = create_message(detected_games_today)

    if not detected_games_today:
        logger.info("There is only one thing we say to death - Not today!")
        sys.exit(0)

    asyncio.run(send(message))
