#!/bin/sh
set -e

export FLASK_APP=web.py
export FLASK_ENV=development

CRON_PATH="/var/spool/cron/crontabs"
CRON_FILE="$CRON_PATH/root"

echo "0 9 * * * python $(readlink -f cron.py)" >> $CRON_FILE
chmod 0600 "$CRON_FILE"

crond -L /var/log/crond -c $CRON_PATH

flask run --host=0.0.0.0 --port=5000

exec "$@"
