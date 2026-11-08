#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from apheleia_project_management import create_containers, export_to_html, import_from_yaml
from apheleia_project_management._utils import set_today


def parse_today(value : (str | None)) -> (pd.Timestamp | None):
    """
    Read the --today option: a date (YYYY-MM-DD) or None for no report date

    :param value: Value given on the command line, or None if it was not given
    :return: Date: the day the report is run if the option was not given, or None for no report date
    """

    if value is None:
        return pd.Timestamp.now().normalize()
    if value.strip().lower() == "none":
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        try:
            return pd.Timestamp(value.strip())
        except ValueError:
            pass
    raise ValueError(f"--today {value!r} is not a date. Use YYYY-MM-DD, e.g. 2026-11-09, or None for a report with no date")

def main():
    parser = argparse.ArgumentParser(description="Apheleia Project Management Report Tool")

    parser.add_argument("--input", type=str, help="Input directory path", default=".")
    parser.add_argument("--html", type=str, help="Output directory path for html", default="./html")
    parser.add_argument("--today", type=str, default=None, metavar="YYYY-MM-DD|None",
                        help="Report date: the day the report is made for (default: the day it is run). Today is marked "
                             "on the charts, forecasts start from it and tasks are checked against it for being stale. "
                             "None gives a report with no date: nothing is marked as today, forecasts start from each "
                             "task's latest status update, and checks use the latest status update in the input")

    args = parser.parse_args()

    try:
        # The report date
        set_today(parse_today(args.today))

        # Parse the input data
        data = import_from_yaml(Path(args.input).resolve())

        # Create data containers
        create_containers(Path(args.html).resolve(), data)
    except ValueError as e:
        print(f"ERROR : {e}", file=sys.stderr)
        sys.exit(1)

    # Export HTML
    export_to_html(Path(args.html).resolve())

if __name__ == "__main__":
  main()
