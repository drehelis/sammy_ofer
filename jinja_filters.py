import datetime

from babel.dates import format_date


def babel_format_day_heb(s):
    day_name = format_date(s, "EEEE", locale="he")
    # Remove "יום" prefix if present
    return day_name.replace("יום ", "")


def babel_format_full_heb(s):
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        return format_date(dt, format="full", locale="he")
    except Exception:
        return s
