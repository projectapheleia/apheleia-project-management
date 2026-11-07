#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from apheleia_project_management import create_containers, export_to_html, import_from_yaml


def main():
    parser = argparse.ArgumentParser(description="Apheleia Project Management Report Tool")

    parser.add_argument("--input", type=str, help="Input directory path", default=".")
    parser.add_argument("--html", type=str, help="Output directory path for html", default="./html")

    args = parser.parse_args()

    try:
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
