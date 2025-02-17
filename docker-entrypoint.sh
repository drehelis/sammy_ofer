#!/bin/sh
set -e

export FLASK_APP=web.py
export FLASK_ENV=development

CRON_PATH="/var/spool/cron/crontabs"
CRON_FILE="$CRON_PATH/root"
CRON_EXPR="0 7 * * *" # UTC

if ! grep -q "cron.py" $CRON_FILE; then
  echo "$CRON_EXPR python $(readlink -f cron.py)" >> $CRON_FILE
  chmod 0600 "$CRON_FILE"
fi

crond -L /var/log/crond -c $CRON_PATH

python3 web.py

exec "$@"
