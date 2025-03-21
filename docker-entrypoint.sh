#!/bin/sh
set -e

python3 app.py

exec "$@"
