# https://marketplace.visualstudio.com/items?itemName=yy0931.vscode-sqlite3-editor

import sqlite3

def db_connection():
    conn = sqlite3.connect('sammy_ofer.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            scraped_date_time TEXT,
            league TEXT,
            home_team TEXT,
            home_team_en TEXT,
            home_team_url TEXT,
            game_hour TEXT,
            guest_team TEXT,
            guest_team_en TEXT,
            guest_team_url TEXT,
            game_time_delta TEXT,
            road_block_time TEXT,
            specs_word TEXT,
            specs_number INTEGER,
            post_specs_number INTEGER,
            poll TEXT,
            notes TEXT,
            specs_emoji TEXT,
            custom_road_block_time TEXT,
            created_at TEXT
        )
    ''')

if __name__ == "__main__":
    init_db()
