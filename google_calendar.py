from datetime import timedelta
from zoneinfo import ZoneInfo
import hashlib
import json
import os.path
from logger import logger

from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.exceptions import MalformedError, RefreshError

from models import unpack_game_data

class GoogleCalendarManager:
    def __init__(self):
        self.calendar_id = 'sammyofernotification@gmail.com'
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.timezone = ZoneInfo("Asia/Jerusalem")
        self.service = None
        self.authenticated = False

    def authenticate(self):
        try:
            with open('service_account.json', 'r') as f:
                creds_dict = json.load(f)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=self.SCOPES
            )
            self.service = build('calendar', 'v3', credentials=credentials)
            self.authenticated = True

        except FileNotFoundError as notfound_error:
            self.authenticated = False
            logger.warning('FileNotFoundError: %s', notfound_error)
        except json.decoder.JSONDecodeError as json_error:
            self.authenticated = False
            logger.error('JSONDecodeError: %s', json_error)

    def create_events(self, payload):
        if not self.authenticated:
            logger.warning('Not going to update Google calendar')
            return
        
        for _, item in payload.items():
            row = unpack_game_data(item)
            
            current_hash = hashlib.sha256(f"{row.league}|{row.home_team}|{row.guest_team}|{row.specs_number}|{row.notes}".encode()).hexdigest()

            start_time = row.scraped_date_time.replace(tzinfo=self.timezone).astimezone(ZoneInfo("UTC")).astimezone(self.timezone).isoformat()
            end_time = (row.scraped_date_time + timedelta(hours=2)).replace(tzinfo=self.timezone).astimezone(ZoneInfo("UTC")).astimezone(self.timezone).isoformat()

            event_data = {
                'summary': f"{self._shorten_team_name(row.home_team)} || {self._shorten_team_name(row.guest_team)} (קהל {row.specs_number:,}~)",
                'location': "איצטדיון סמי עופר - רח' רוטנברג 2, חיפה",
                'description': current_hash,
                'start': {
                    'dateTime': row.scraped_date_time.isoformat(),
                    'timeZone': 'Asia/Jerusalem',
                },
                'end': {
                    'dateTime': (row.scraped_date_time + timedelta(hours=2)).isoformat(),
                    'timeZone': 'Asia/Jerusalem',
                },
                'transparency': 'transparent',
                'visibility': 'public',
                'colorId': '11' if row.home_team == 'הפועל חיפה' else '10' if row.home_team == 'מכבי חיפה' else '5'
            }
            
            try:
                list_event = self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True
                ).execute()
            except RefreshError as refresh_error:
                logger.error('RefreshError: %s', refresh_error)
                return

            if not list_event.get('items'):
                new_event = self.service.events().insert(calendarId=self.calendar_id, body=event_data).execute()
                logger.info(f'Calendar event created: {new_event.get("htmlLink")}')
                continue

            event_id = list_event['items'][0]['id']
            event_hash = list_event['items'][0]['description']
            
            if current_hash != event_hash:
                updated_event = self.service.events().update(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=event_data
                ).execute()
                logger.info(f"Calendar event updated: {updated_event.get('htmlLink')}")

    def _shorten_team_name(self, team: str) -> str:
        return f"{team[0]}. {team.split(' ', 1)[1]}" if ' ' in team else team
