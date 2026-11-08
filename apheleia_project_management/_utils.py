import re

import pandas as pd

# Get today's date - save in case script cross day boundary
today = pd.Timestamp.now().normalize()
default_end_date = today + pd.Timedelta(days=365)

def smart_date_converter(value : (str | None)) -> (str | pd.Timestamp | None):
    """
    Attempts to convert a string to a datetime object if it matches
    the YYYY-MM-DD format. Otherwise, returns the original value.

    :param value: str
    :type value: str | None
    :return: str | pd.Timestamp | None
    :rtype: str | pd.Timestamp | None
    """
    if not isinstance(value, str) or re.fullmatch(r"M\d+", value):
        return value

    val= value.strip().lower()
    if val in ["", "none", "nan", "null"]:
        return None

    try:
        return pd.to_datetime(value, errors='raise')
    except (ValueError, TypeError):
        return value

def milestone_badges(dates) -> list:
    """
    Html badges saying whether each milestone has passed, is current or is upcoming.

    The current milestone is the next one due, i.e. the first dated today or later. The dates are
    those of a single project, in any order.

    :param dates: Milestone dates
    :type dates: iterable
    :return: List of html strings, one per date, in the same order as the dates
    :rtype: list
    """

    dates = pd.Series(pd.to_datetime(list(dates), errors="coerce"))
    upcoming = dates[dates >= today]
    current = upcoming.idxmin() if len(upcoming) else None

    badges = []
    for i, d in dates.items():
        if pd.isna(d):
            badges.append("")
        elif i == current:
            badges.append('<span class="badge badge-current">&#9679; Current milestone</span>')
        elif d < today:
            badges.append('<span class="badge badge-passed">Passed</span>')
        else:
            badges.append('<span class="badge badge-upcoming">Upcoming</span>')
    return badges

def milestone_dates_text(start, end) -> list:
    """
    Text for the date of each milestone, for tables.

    A milestone on a single date is that date. A milestone with a start and end date shows both,
    as "<start> to <end>". The end date is the date the milestone is due.

    :param start: Start date of each milestone (missing for a single date milestone)
    :type start: iterable
    :param end: End date of each milestone, or its only date
    :type end: iterable
    :return: List of strings, one per milestone
    :rtype: list
    """

    text = []
    for s, e in zip(pd.to_datetime(list(start), errors="coerce"), pd.to_datetime(list(end), errors="coerce"), strict=True):
        if pd.isna(e):
            text.append("")
        elif pd.isna(s):
            text.append(f"{e:%Y-%m-%d}")
        else:
            text.append(f"{s:%Y-%m-%d} to {e:%Y-%m-%d}")
    return text

def value_to_filename(value : str) -> str:
    """
    Convert a string to a valid filename

    :param value: str
    :type value: str
    :return: str
    """
    s = value
    s = s.lower()
    s = s.replace(" ", "_")

    return s

__all__ = [
    "today",
    "smart_date_converter",
    "milestone_badges",
    "milestone_dates_text",
    "value_to_filename"
]
