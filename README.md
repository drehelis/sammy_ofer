# Sammy Ofer Notification Bot 🤖

[!["Buy Me A Coffee"](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee&style=plastic)](https://www.buymeacoffee.com/drehelis)
![Telegram](https://img.shields.io/endpoint?color=neon&style=plastic&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2Fsammy_ofer_notification_channel)

## Description

A small time scheduled (cron) _web-scraper_ to notify of upcoming game events taking place in [Sammy Ofer Stadium](https://www.haifa-stadium.com/ "Sammy Ofer Stadium").

Join the notification #channel on [Telegram](https://t.me/sammy_ofer_notification_channel) and enjoy:

* Single notification for the upcoming event
* Matchup, average attendance and roadblock times
* Spam free service
* Static landing page to be shown on big screen/TV

## Web-UI

![Web-UI screenshot](screen.png)

## Static landing page ([link](https://drehelis.github.io/sammy_ofer/static.html))

![Static screenshot](static.jpeg)

## Build it
```
git clone https://github.com/autogun/sammy_ofer.git
cd sammy_ofer
docker build . -t sammy_ofer
```

## Run it
```
docker run -d --name sammy_ofer \
    --publish 5000:5000 \
    --restart=on-failure \
    --env TELEGRAM_CHANNEL_ID=<required> \
    --env TELEGRAM_TOKEN=<required> \
    --env GH_PAT (optional) \
    sammy_ofer:latest
```

## Debug
```
pip install -r requirements.txt
flask run --port=5001
```

## TODO

- [ ] Cron configuation (some sort of UI?)
- [ ] **Delete** option currently does absolutely nothing
- [ ] Use SQLite instead of a dictionary file
