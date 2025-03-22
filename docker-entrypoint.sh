#!/bin/sh
set -e

python3 run.py

exec "$@"
