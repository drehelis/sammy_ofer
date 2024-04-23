from babel.dates import format_date


def babel_format_day_heb(s):
    return format_date(s, "EEEE", locale="he")


def babel_format_full_heb(s):
    return format_date(s, format="full", locale="he")
