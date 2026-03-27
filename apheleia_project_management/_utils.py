import pandas as pd
import re

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
    "value_to_filename"
]
