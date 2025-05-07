# Sammy Ofer Notification Bot 🤖

[!["Buy Me A Coffee"](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee&style=plastic)](https://www.buymeacoffee.com/drehelis)
[![Telegram](https://img.shields.io/endpoint?color=neon&style=plastic&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2Fsammy_ofer_notification_channel&label=Sammy%20Ofer%20Notification%20Channel)](https://t.me/sammy_ofer_notification_channel)
[![Calendar](https://img.shields.io/badge/-Sammy_Ofer_Notification_Calendar-gray?logo=googlecalendar&style=plastic&logoColor=e9ff70)](https://yeshmishak.top/cal.html)

## Description

A small time scheduled (cron) _web-scraper_ to notify of upcoming game events taking place in [Sammy Ofer Stadium](https://www.haifa-stadium.com/ "Sammy Ofer Stadium").

Join the notification #channel on [Telegram](https://t.me/sammy_ofer_notification_channel) and enjoy:

* ☝️ Single notification for the upcoming event
* 🚦 Matchup, average attendance and roadblock times
* ⛔ Spam free service
* 🌎 Static landing page to be shown on big screen/TV
* 🗓️ Public Google Calendar

## Web-UI

![Web-UI screenshot](screen.png)

## Static landing page ([link](https://drehelis.github.io/sammy_ofer/static.html))

![Static screenshot](static.jpeg)

## Google Calendar

![Google Calendar](google_calendar.png)

## Build it
```
git clone https://github.com/autogun/sammy_ofer.git
cd sammy_ofer
docker build . -t sammy_ofer
```

## Run it
```
cat << EOF > .env
TELEGRAM_CHANNEL_ID=<required>
TELEGRAM_TOKEN=<required>
GH_PAT=(optional)
SKIP_COMMIT=false
SKIP_CALENDAR=false
EOF

docker run -d --name sammy_ofer \
    --publish 5000:5000 \
    --restart=on-failure \
    --env-file ./.env \
    --volume $(PWD)/service_account.json:/usr/src/sammy_ofer/service_account.json \
    --volume $(PWD)/sammy_ofer.db:/usr/src/sammy_ofer/sammy_ofer.db \
    sammy_ofer:latest
```

## Debug
```
uv pip install -r requirements.txt
flask run --debug --port=5001
```

Manually run cron job
```
python -c "from scheduler import run_job; run_job()"
```

## TODO
I'm out of ideas...

- [x] ~~Use SQLite instead of a dictionary file~~
- [x] ~~**Delete** option currently does absolutely nothing~~
- [x] ~~Cron configuation (some sort of UI?)~~
