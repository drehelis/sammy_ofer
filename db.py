import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from logger import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sammy_ofer.db")

FIELDS_TO_COMPARE = [
    "scraped_date_time",
    "home_team",
    "home_team_en",
    "game_hour",
    "guest_team",
    "guest_team_en",
    "specs_word",
    "sched_time",
    "specs_number",
    "post_specs_number",
    "poll",
    "notes",
    "specs_emoji",
    "custom_road_block_time",
]


@contextmanager
def db_transaction():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception as err:
        conn.rollback()
        raise err
    finally:
        conn.close()


def update_db_record(
    id, sched_time, number, post_number, word, poll, notes, updated_at
):
    with db_transaction() as (conn, cursor):
        cursor.execute(
            """
            UPDATE games SET
                sched_time = ?,
                specs_number = ?,
                post_specs_number = ?,
                specs_word = ?,
                poll = ?,
                notes = ?,
                updated_at = ?
            WHERE game_id = ?
        """,
            (sched_time, number, post_number, word, poll, notes, updated_at, id),
        )

    return cursor.rowcount > 0


def delete_db_record(id):
    with db_transaction() as (conn, cursor):
        cursor.execute("DELETE FROM games WHERE game_id = ?", (id,))

    return cursor.rowcount > 0


def add_db_record(fields):
    game_date, game_time = fields.pop("game_date"), fields.pop("game_time")
    scraped_date_time = f"{game_date}T{game_time}:00"
    game_id = hashlib.sha1(scraped_date_time.encode()).hexdigest()

    fields["scraped_date_time"] = scraped_date_time
    fields["game_hour"] = game_time
    fields["game_id"] = game_id
    fields["created_at"] = datetime.now().isoformat()

    columns = ", ".join(fields.keys())
    placeholders = ", ".join(["?" for _ in fields])
    values = list(fields.values())

    with db_transaction() as (conn, cursor):
        query = f"""
            INSERT INTO games
            ({columns})
            VALUES ({placeholders})
        """
        cursor.execute(query, values)

    return cursor.rowcount > 0


def check_for_field_update(games):
    fields_str = ", ".join(FIELDS_TO_COMPARE)

    with db_transaction() as (conn, cursor):
        query = f"""
        SELECT
            {fields_str}
        FROM games WHERE game_id = ?
        """

        cursor.execute(query, (games.game_id,))
        existing = cursor.fetchone()

        if not existing:
            return None

        db_values = dict(existing)

        changes = {}
        for field in FIELDS_TO_COMPARE:
            db_value = db_values.get(field)
            web_value = getattr(games, field)

            if isinstance(web_value, datetime):
                web_value = web_value.isoformat()

            if str(db_value) != str(web_value):
                changes[field] = {"db": db_value, "web": web_value}

        if changes:
            logger.info(f"Changes detected for game {games.game_id}:")
            for field, values in changes.items():
                logger.info(
                    f"Field: [{field}] '{values['db']} (db)' → '{values['web']} (web)'"
                )

            return True
        return False


def store_scraped_games_in_db(games):
    with db_transaction() as (conn, cursor):
        for game_data in games:
            update_required = check_for_field_update(game_data)

            if update_required:
                logger.info("Updating existing game record")
                cursor.execute(
                    """
                    UPDATE games SET
                        scraped_date_time = ?,
                        league = ?,
                        home_team = ?,
                        home_team_en = ?,
                        home_team_url = ?,
                        game_hour = ?,
                        guest_team = ?,
                        guest_team_en = ?,
                        guest_team_url = ?,
                        game_time_delta = ?,
                        road_block_time = ?,
                        specs_word = ?,
                        sched_time = ?,
                        specs_number = ?,
                        post_specs_number = ?,
                        poll = ?,
                        notes = ?,
                        specs_emoji = ?,
                        custom_road_block_time = ?,
                        created_at = ?,
                        updated_at = ?
                    WHERE game_id = ?
                """,
                    (
                        game_data.scraped_date_time.isoformat()
                        if isinstance(game_data.scraped_date_time, datetime)
                        else str(game_data.scraped_date_time),
                        game_data.league,
                        game_data.home_team,
                        game_data.home_team_en,
                        game_data.home_team_url,
                        game_data.game_hour,
                        game_data.guest_team,
                        game_data.guest_team_en,
                        game_data.guest_team_url,
                        game_data.game_time_delta.isoformat()
                        if isinstance(game_data.game_time_delta, datetime)
                        else str(game_data.game_time_delta),
                        game_data.road_block_time,
                        game_data.specs_word,
                        game_data.sched_time,
                        game_data.specs_number,
                        game_data.post_specs_number,
                        game_data.poll,
                        game_data.notes,
                        game_data.specs_emoji,
                        game_data.custom_road_block_time,
                        datetime.now().isoformat(),
                        game_data.updated_at,
                        game_data.game_id,
                    ),
                )
            elif update_required is None:
                cursor.execute(
                    """
                INSERT INTO games
                (game_id, scraped_date_time, league, home_team, home_team_en, home_team_url,
                    game_hour, guest_team, guest_team_en, guest_team_url, game_time_delta,
                    road_block_time, specs_word, sched_time, specs_number, post_specs_number,
                    poll, notes, specs_emoji, custom_road_block_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        game_data.game_id,
                        game_data.scraped_date_time.isoformat()
                        if isinstance(game_data.scraped_date_time, datetime)
                        else str(game_data.scraped_date_time),
                        game_data.league,
                        game_data.home_team,
                        game_data.home_team_en,
                        game_data.home_team_url,
                        game_data.game_hour,
                        game_data.guest_team,
                        game_data.guest_team_en,
                        game_data.guest_team_url,
                        game_data.game_time_delta.isoformat()
                        if isinstance(game_data.game_time_delta, datetime)
                        else str(game_data.game_time_delta),
                        game_data.road_block_time,
                        game_data.specs_word,
                        game_data.sched_time,
                        game_data.specs_number,
                        game_data.post_specs_number,
                        game_data.poll,
                        game_data.notes,
                        game_data.specs_emoji,
                        game_data.custom_road_block_time,
                        datetime.now().isoformat(),
                    ),
                )


def get_all_db_entries():
    with db_transaction() as (conn, cursor):
        current_time = datetime.now(ZoneInfo("Asia/Jerusalem")).isoformat()

        cursor.execute(
            """
            SELECT * FROM games
            WHERE scraped_date_time >= ?
            ORDER BY scraped_date_time ASC
        """,
            (current_time,),
        )

        upcoming_games = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT * FROM games
            WHERE scraped_date_time < ?
            ORDER BY scraped_date_time DESC
        """,
            (current_time,),
        )

        passed_games = [dict(row) for row in cursor.fetchall()]

        return upcoming_games, passed_games


def get_game_details(game_id):
    with db_transaction() as (conn, cursor):
        cursor.execute(
            """
            SELECT * FROM games
            WHERE game_id = ?
        """,
            (game_id,),
        )

        result = cursor.fetchone()

        if result:
            return dict(result)
