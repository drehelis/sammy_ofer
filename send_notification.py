#!/usr/bin/env python3

import datetime
import os
from pathlib import Path
from random import choice
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Bot, constants
from telegram.helpers import escape_markdown

import web_scrape
from logger import logger
from metadata import EMOJI_HEARTS, POLL_SENTENCES
from models import unpack_game_data

load_dotenv()


assert "TELEGRAM_CHANNEL_ID" in os.environ and "TELEGRAM_TOKEN" in os.environ, (
    "Both 'TELEGRAM_CHANNEL_ID' and 'TELEGRAM_TOKEN' env. variables must be set."
)

TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

absolute_path = Path(__file__).resolve().parent


def random_choice(rand):
    return choice(rand)


def check_games_today(all_db_entries):
    today = datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).date()

    upcoming, passed = all_db_entries
    for obj in upcoming + passed:
        scraped_date_time = datetime.datetime.fromisoformat(
            obj["scraped_date_time"]
        ).date()
        if today == scraped_date_time:
            yield obj

    return False


def escape_markdown_v2(text):
    return escape_markdown(text, version=2)


def create_message(obj_data):
    for item in obj_data:
        row = unpack_game_data(item.values())

        yield (
            f"""
משחק ⚽ *היום* בשעה *{row.game_hour}*
*{row.league}*: [{escape_markdown_v2(row.home_team)}]({row.home_team_url}) \\|\\| [{escape_markdown_v2(row.guest_team)}]({row.guest_team_url})
צפי חסימת כבישים: *{row.custom_road_block_time}*
צפי אוהדים משוער: *{row.specs_word}* {escape_markdown_v2(f"({row.specs_number:,})")} {row.specs_emoji}

🚦 *מצב התנועה בזמן אמת*:
[גוגל מפות](https://www.google.com/maps/@32.785090452228864,34.96269433141559,15z/data=!5m1!1e1)
[וייז Waze](https://www.waze.com/he/live-map/directions?to=ll.32.78507,34.962766)

""",
            (
                row.scraped_date_time,
                row.home_team,
                row.guest_team,
                row.poll,
                escape_markdown_v2(row.notes),
            ),
        )


async def send(msg, token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHANNEL_ID):
    async with Bot(token) as bot:
        for iterator in msg:
            send_message = list(iterator[:-1])
            iterated_data = iterator[-1]

            scraped_date_time, home_team, guest_team, poll, notes = iterated_data

            if notes:
                send_message.append(f"📣: {notes}\n\n")

            send_message.append(
                f"_השירות מובא ב {random_choice(EMOJI_HEARTS)} לתושבי חיפה_"
            )
            send_message.append("\n\n")
            send_message.append(
                escape_markdown_v2("https://t.me/sammy_ofer_notification_channel")
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
                    [home_team, guest_team],
                    disable_notification=True,
                    protect_content=True,
                    close_date=datetime.datetime.fromisoformat(
                        scraped_date_time
                    ).timestamp(),
                )
                logger.info("Telegram poll sent!")
