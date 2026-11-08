import re

import pandas as pd

HORIZON = pd.Timedelta(days=365)
""" How far past the report date charts draw items that have no end date """

_dates = {
    "today" : pd.Timestamp.now().normalize(),
    "latest_update" : None,
    "latest_date" : None,
}
""" The report date (None for none), the latest status update and the latest date anywhere in the input """

def set_today(value) -> None:
    """
    Set the report date: the day the report is made for. By default it is the day the report is run.

    With no report date (None) nothing is marked as today and forecasts start from the latest status update of each
    task. Checks that need a current date (stale tasks, the current milestone, availability now) use the latest status
    update in the input instead.

    :param value: Date (anything pandas reads as a date), or None for no report date
    :return: None
    """

    _dates["today"] = None if value is None else pd.Timestamp(value).normalize()

def set_data_dates(latest_update, latest_date) -> None:
    """
    Record the latest status update and the latest date in the input, which stand in for the report date when there is none

    :param latest_update: Latest status update of any task, or None
    :param latest_date: Latest date anywhere in the input, or None
    :return: None
    """

    _dates["latest_update"] = None if latest_update is None or pd.isna(latest_update) else pd.Timestamp(latest_update).normalize()
    _dates["latest_date"] = None if latest_date is None or pd.isna(latest_date) else pd.Timestamp(latest_date).normalize()

def today() -> (pd.Timestamp | None):
    """
    The report date

    :return: The report date, or None if the report has none
    """

    return _dates["today"]

def reference_date() -> (pd.Timestamp | None):
    """
    The date checks are made against: the report date, or the latest status update in the input if there is no report date

    :return: Date, or None if there is no report date and no status update
    """

    return _dates["today"] if _dates["today"] is not None else _dates["latest_update"]

def reference_text() -> str:
    """
    Text naming the date checks are made against, e.g. "today (2026-11-09)"

    :return: str
    """

    if _dates["today"] is not None:
        return f"the report date ({_dates['today']:%Y-%m-%d})"
    if _dates["latest_update"] is not None:
        return f"the latest status update ({_dates['latest_update']:%Y-%m-%d}), as the report has no date"
    return "nothing, as the report has no date and there are no status updates"

def today_text() -> str:
    """
    The report date as text, or a note that there is none

    :return: str
    """

    if _dates["today"] is not None:
        return f"{_dates['today']:%Y-%m-%d}"
    if _dates["latest_update"] is not None:
        return f"none (as of the latest status update, {_dates['latest_update']:%Y-%m-%d})"
    return "none"

def today_markers() -> dict:
    """
    Markers for a chart: today, if the report has a date

    :return: Dictionary of marker name to date
    """

    return {"Today" : _dates["today"]} if _dates["today"] is not None else {}

def default_end_date() -> pd.Timestamp:
    """
    End date given to items that have none, so that they can be drawn: a year after the report date, or after the latest
    status update, or the latest date in the input, if there is no report date

    :return: Date
    """

    anchor = reference_date()
    if anchor is None:
        anchor = _dates["latest_date"] if _dates["latest_date"] is not None else pd.Timestamp.now().normalize()
    return anchor + HORIZON

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

    The current milestone is the next one due, i.e. the first dated on or after the reference date (see
    reference_date). The dates are
    those of a single project, in any order.

    :param dates: Milestone dates
    :type dates: iterable
    :return: List of html strings, one per date, in the same order as the dates
    :rtype: list
    """

    dates = pd.Series(pd.to_datetime(list(dates), errors="coerce"))
    now = reference_date()
    if now is None:
        return ["" for _ in dates]
    upcoming = dates[dates >= now]
    current = upcoming.idxmin() if len(upcoming) else None

    badges = []
    for i, d in dates.items():
        if pd.isna(d):
            badges.append("")
        elif i == current:
            badges.append('<span class="badge badge-current">&#9679; Current milestone</span>')
        elif d < now:
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

DAYS_PER_WEEK = 5
""" Man-days in a man-week """

DAYS_PER_MONTH = 20
""" Man-days in a man-month """

MONTHS_PER_YEAR = 12
""" Man-months in a man-year """

EFFORT_UNITS = {"md" : 1 / DAYS_PER_MONTH, "mw" : DAYS_PER_WEEK / DAYS_PER_MONTH, "mm" : 1.0, "my" : float(MONTHS_PER_YEAR)}
""" Man-months in one of each unit of effort """

UNIT_NAMES = {"md" : "man-days", "mw" : "man-weeks", "mm" : "man-months", "my" : "man-years"}
""" Name of each unit of effort """

_EFFORT = re.compile(r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([A-Za-z-]*)\s*")

def parse_effort(value, where : str, default_unit : (str | None) = None, allow_zero : bool = False) -> (float | None):
    """
    Convert an effort to man-months

    An effort is a number followed by a unit: md (man-days), mw (man-weeks), mm (man-months) or my (man-years), e.g.
    "5 mm". Whitespace between the number and unit is optional and the unit is not case sensitive.
    A man-week is 5 man-days, a man-month 20 man-days and a man-year 12 man-months.

    :param value: Effort as given in the input, or None / empty for none
    :param where: What the value is, for error messages, e.g. "workpackage WP1 estimate '5'"
    :type where: str
    :param default_unit: Unit of a number given without one. If None a unit must be given
    :type default_unit: str | None
    :param allow_zero: Whether 0 is allowed. Negative values never are
    :type allow_zero: bool
    :return: Effort in man-months, or None if there is none
    :rtype: float | None
    """

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    units = ", ".join(EFFORT_UNITS)
    names = ", ".join(f"{u} ({n})" for u, n in UNIT_NAMES.items())
    example = '"5 mm"'

    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if not (is_number or isinstance(value, str)) or (is_number and default_unit is None):
        raise ValueError(f"{where} must be a number followed by a unit ({units}), e.g. {example}")

    if is_number:
        number, unit = float(value), default_unit
    else:
        if value.strip() == "":
            return None
        m = _EFFORT.fullmatch(value)
        if m is None:
            raise ValueError(f"{where} is not understood. It must be a number followed by a unit ({units}), e.g. {example}")
        number, unit = float(m.group(1)), m.group(2).lower() or default_unit
        if unit is None:
            raise ValueError(f"{where} has no unit. Use {names}, e.g. {example}")
        if unit not in EFFORT_UNITS:
            raise ValueError(f"{where} has unknown unit {m.group(2)!r}. Use {names}")

    if number < 0 or (number == 0 and not allow_zero):
        raise ValueError(f"{where} must not be negative" if allow_zero else f"{where} must be greater than 0")

    return number * EFFORT_UNITS[unit]

def format_months(months : float) -> str:
    """
    Html for an effort in man-months

    The page has a select box for the unit of effort, which rewrites the text of these spans.

    :param months: Effort in man-months
    :type months: float
    :return: Html such as <span class="effort" data-mm="5.000000">5 mm</span>
    :rtype: str
    """
    text = f"{months:.2f}".rstrip("0").rstrip(".")
    if text in ("", "-0"):
        text = "0"
    return f'<span class="effort" data-mm="{months:.6f}">{text} mm</span>'

def format_days(days : float) -> str:
    """
    Html for an effort in man-days, which the page shows in the unit chosen in its Units box

    :param days: Effort in man-days
    :type days: float
    :return: Html, see format_months
    :rtype: str
    """
    return format_months(days / DAYS_PER_MONTH)

def with_columns(df : pd.DataFrame, columns : list) -> pd.DataFrame:
    """
    Copy of a dataframe with any of the columns it does not have added at the end, empty, and the index reset

    The same as concatenating an empty dataframe with the columns, which pandas has deprecated

    :param df: Dataframe
    :type df: pd.DataFrame
    :param columns: Columns the result must have
    :type columns: list
    :return: Dataframe with at least the columns
    :rtype: pd.DataFrame
    """

    out = df.reset_index(drop=True)
    for col in columns:
        if col not in out.columns:
            out[col] = pd.Series(None, index=out.index, dtype=object)
    return out

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
    "set_today",
    "set_data_dates",
    "reference_date",
    "reference_text",
    "today_text",
    "today_markers",
    "default_end_date",
    "smart_date_converter",
    "milestone_badges",
    "milestone_dates_text",
    "value_to_filename",
    "parse_effort",
    "format_months",
    "format_days",
    "EFFORT_UNITS",
    "UNIT_NAMES",
    "DAYS_PER_WEEK",
    "DAYS_PER_MONTH",
    "MONTHS_PER_YEAR",
]
