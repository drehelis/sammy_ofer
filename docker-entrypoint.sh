#!/bin/sh
set -e

export FLASK_APP=web.py
export FLASK_ENV=development

CRON_FILE="/var/spool/cron/crontabs/sammy_ofer"

echo "0 8 * * * python $(readlink -f cron.py)" > $CRON_FILE
chmod 0600 "$CRON_FILE"

crond -l 8 -d 8 -L /var/log/crond

flask run --host=0.0.0.0 --port=5000

exec "$@"