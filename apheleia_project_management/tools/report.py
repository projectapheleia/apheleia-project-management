#!/usr/bin/env python3
import argparse
from pathlib import Path

from apheleia_project_management import import_from_yaml, create_containers, export_to_html

def main():
    parser = argparse.ArgumentParser(description="Apheleia Project Management Report Tool")

    parser.add_argument("--input", type=str, help="Input directory path", default=".")
    parser.add_argument("--html", type=str, help="Output directory path for html", default="./html")

    args = parser.parse_args()

    # Parse the input data
    data = import_from_yaml(Path(args.input).resolve())

    # Create data containers
    create_containers(Path(args.html).resolve(), data)

    # Export HTML
    export_to_html()

if __name__ == "__main__":
  main()
