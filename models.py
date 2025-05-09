from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GameData:
    id: int
    game_id: str
    scraped_date_time: datetime
    league: str
    home_team: str
    home_team_en: str
    home_team_url: str
    game_hour: str
    guest_team: str
    guest_team_en: str
    guest_team_url: str
    game_time_delta: datetime
    road_block_time: str
    specs_word: str
    sched_time: str
    specs_number: int
    post_specs_number: int
    poll: Optional[str]
    notes: str
    specs_emoji: str
    custom_road_block_time: str
    created_at: datetime
    updated_at: datetime


def unpack_game_data(item_tuple: tuple) -> GameData:
    return GameData(*item_tuple)
