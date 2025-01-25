#!/usr/bin/env python3

from pathlib import Path
from random import choice
import asyncio
import datetime
import json
import os
import sys
import argparse  # ADDED: Argument parser for early/standard bot distinction

from dotenv import load_dotenv

from telegram import Bot, constants
from telegram.helpers import escape_markdown

from logger import logger
import web_scrape

from metadata import EMOJI_HEARTS, POLL_SENTENCES

BIG_GAME_TH = 10000

load_dotenv()


if "TELEGRAM_CHANNEL_ID" not in os.environ or "TELEGRAM_TOKEN" not in os.environ:
    logger.info(
        "Both 'TELEGRAM_CHANNEL_ID' and 'TELEGRAM_TOKEN' env. variables must be set."
    )
    sys.exit(1)

TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")  # Standard bot channel
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Standard bot token
EARLY_BOT_CHANNEL_ID = os.getenv("TELEGRAM_EARLY_CHANNEL_ID")  # ADDED: Early bot channel ID
EARLY_BOT_TOKEN = os.getenv("TELEGRAM_EARLY_BOT_TOKEN")  # ADDED: Early bot token
absolute_path = Path(__file__).resolve().parent


def random_choice(rand):
    return choice(rand)


def check_games_today(games):
    # Set today to datetime.date(YEAR, M, D) when debugging specific date
    today = datetime.date.today()

    if not isinstance(games, str):
        for _, value in games.items():
            if today == value[0].date():
                logger.info("Yesh mishak!")
                yield value

    return False

def escape_markdown_v2(text):
    return escape_markdown(text, version=2)

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
*{league}*: [{escape_markdown_v2(home_team)}]({home_team_url}) \\|\\| [{escape_markdown_v2(guest_team)}]({guest_team_url})
צפי חסימת כבישים: *{custom_road_block_time}*
צפי אוהדים משוער: *{specs_word}* {custom_sepcs_number}

""", (
            scraped_date_time,
            home_team,
            guest_team,
            poll,
            escape_markdown_v2(notes),
        )


async def send(msg, token, chat_id, bot_type):  # CHANGED: Added bot_type for logging
    """Send a message using the Telegram bot."""
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
        logger.info(f"Telegram message sent to {bot_type} bot!")  # CHANGED: Log bot type

        if poll == "on":
            await bot.sendPoll(
                chat_id,
                random_choice(POLL_SENTENCES),
                json.dumps([home_team, guest_team]),
                disable_notification=True,
                protect_content=True,
                close_date=datetime.datetime.timestamp(scraped_date_time),
            )
            logger.info(f"Telegram poll sent to {bot_type} bot!")  # CHANGED: Log bot type


if __name__ == "__main__":
    # ADDED: Argument parsing to distinguish between early and standard bots
    parser = argparse.ArgumentParser(description="Run Telegram bot notifier.")
    parser.add_argument(
        "--early", action="store_true", help="Run the early bot (e.g., 4 AM local time)"
    )
    parser.add_argument(
        "--standard", action="store_true", help="Run the standard bot (e.g., 7 AM local time)"
    )
    args = parser.parse_args()

    # Determine bot type and configuration
    if args.standard:
        logger.info("Running standard bot...")
        bot_type = "standard"
        token = TELEGRAM_TOKEN
        channel_id = TELEGRAM_CHANNEL_ID
    elif args.early:
        logger.info("Running early bot...")
        bot_type = "early"
        token = EARLY_BOT_TOKEN
        channel_id = EARLY_BOT_CHANNEL_ID

    else:
        logger.error("No bot type specified. Use --early or --standard.")
        sys.exit(1)


    web = web_scrape.WebScrape()
    scrape = web.scrape()
    scraped_games = web.decoratored_games(
        scrape
    )  # also fetches teams logos and generates static page
    generated_data = check_games_today(scraped_games)

    # Standard bot logic
    detected_games_today = list(generated_data)
    message = create_message(detected_games_today)

    if not detected_games_today:
        logger.info("There is only one thing we say to death - Not today!")
        sys.exit(0)


    # Standard bot: Notify for all detected games
    if bot_type=="standard":
        message = create_message(detected_games_today)
        asyncio.run(send(message, token, channel_id, bot_type))

    # Early bot: Notify only for games with >10,000 spectators
    elif bot_type == "early":
        filtered_games = [
            game
            for game in detected_games_today
            if int(
                game[-2]
                .replace("\\", "")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
            )
               > BIG_GAME_TH # alert only for 10K or more, which implies a parking problem
        ]
        if filtered_games:
            message = create_message(filtered_games)
            asyncio.run(send(message, token, channel_id, bot_type))
        else:
            logger.info("No games above the 10,000 spectators threshold for early bot.")
