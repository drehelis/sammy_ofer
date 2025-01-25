#!/bin/sh
set -e

export FLASK_APP=web.py
export FLASK_ENV=development

CRON_PATH="/var/spool/cron/crontabs"
CRON_FILE="$CRON_PATH/root"

# Define CRON expressions for early and standard runs
# Local time in Israel, changes on `Dockerfile` ensures it
CRON_EXPR_EARLY="0 4 * * *"   # Runs at 4:00 AM Israel time
CRON_EXPR_STANDARD="0 7 * * *" # Runs at 7:00 AM Israel time

if ! grep -q "cron.py --early" $CRON_FILE; then
  echo "$CRON_EXPR_EARLY python $(readlink -f cron.py) --early" >> $CRON_FILE
fi

if ! grep -q "cron.py --standard" $CRON_FILE; then
  echo "$CRON_EXPR_STANDARD python $(readlink -f cron.py) --standard" >> $CRON_FILE
fi

crond -L /var/log/crond -c $CRON_PATH

python3 web.py

exec "$@"
