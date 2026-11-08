
import sys
from pathlib import Path

import pandas as pd
import yaml

from . import _format
from ._containers import containers
from ._html import HTML
from ._milestones import Milestones
from ._projects import Projects
from ._resources import Resources
from ._tasks import Tasks
from ._utils import set_data_dates, smart_date_converter
from ._workpackages import WorkPackages

# Add version
__version__: str = "0.2.0"

NOT_DATES = {"estimate"}
""" Fields of a definition that are never converted to dates """

def import_from_yaml(path : Path) -> None:
    """
    Import data from all found yaml files

    :param path: Path to yaml files
    :type path: Path
    :return: None
    """

    # All data imported from all yaml files
    data = {
        "milestones" : [],
        "resources" : [],
        "projects" : [],
        "workpackages" : [],
        "tasks" : [],
    }

    types = {f"{k}_definitions" : k for k in data}

    # How the report looks. These are not project data, so their values are used as they are
    look = {"format" : [], "themes" : []}
    types.update({f"{k}_definitions" : k for k in look})
    found = 0

    for file_path in sorted(path.rglob("*.yaml")):
        with open(file_path) as f:
            try:
                content = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"{file_path}: not valid YAML: {e}") from e

        if not isinstance(content, dict) or "type" not in content:
            continue

        k = types.get(content["type"])
        if k is None:
            print(f"WARNING : {file_path}: unknown type {content['type']!r} - file ignored. "
                  f"Expected one of: {', '.join(types)}", file=sys.stderr)
            continue

        if k == "format":
            # A single mapping, or a list of them
            items = content.get("data") or {}
            items = items if isinstance(items, list) else [items]
            if not all(isinstance(d, dict) for d in items):
                raise ValueError(f"{file_path}: data must be a mapping of format settings")
            found += 1
            look[k] += [{**d, _format.SOURCE : file_path} for d in items]
            continue

        definitions = content.get("data") or []
        if not isinstance(definitions, list) or not all(isinstance(d, dict) for d in definitions):
            raise ValueError(f"{file_path}: data must be a list of {k} definitions")

        found += 1
        if k == "themes":
            look[k] += [{**d, _format.SOURCE : file_path} for d in definitions]
            continue

        # Estimates are effort, not dates, so they are kept as given: "3 hours" would otherwise be read as a time
        for d in definitions:
            data[k].append({_k : _v if _k in NOT_DATES else smart_date_converter(_v) for _k, _v in d.items()})

    if found == 0:
        print(f"WARNING : no input files found in {path}", file=sys.stderr)

    data.update(look)
    return data

def create_containers(path : Path, data : dict[str, dict]) -> None:
    """
    Create containers from imported data

    :param path: Path to containers
    :type path: Path
    :param data: Data to create containers from
    :type data: dict[str, dict]
    :return: None
    """

    # How the report looks
    _format.use(_format.configure(data.get("format", []), data.get("themes", [])))

    # Create container classes and import data
    for k,v in data.items():
        if k in ("format", "themes"):
            continue
        if k == "milestones":
            c = Milestones("index", path / k)
        elif k == "resources":
            c = Resources("index", path / k)
        elif k == "projects":
            c = Projects("index", path / k)
        elif k == "workpackages":
            c = WorkPackages("index", path / k)
        elif k == "tasks":
            c = Tasks("index", path / k)
        else:
            raise ValueError(f"Unknown container type: {k}")

        # Import data
        c.import_data(v)

    # Dates that stand in for the report date when it has none
    set_data_dates(latest_update(), latest_date(data))

def latest_update() -> (pd.Timestamp | None):
    """
    Latest status update of any task

    :return: Date, or None if there are no status updates
    """

    index = containers.get("tasks", {}).get("index")
    if index is None or index.imported_df is None or index.imported_df.empty:
        return None
    return pd.to_datetime(index.imported_df["status.date"]).max()

def latest_date(value) -> (pd.Timestamp | None):
    """
    Latest date anywhere in the imported data

    :param value: Imported data (dictionaries and lists of definitions)
    :return: Date, or None if there are no dates
    """

    if isinstance(value, pd.Timestamp):
        return value
    items = value.values() if isinstance(value, dict) else value if isinstance(value, list) else []
    dates = [d for d in (latest_date(v) for v in items) if d is not None and pd.notna(d)]
    return max(dates) if dates else None

def export_to_html(path : Path):
    """
    Export all containers to html

    :param path: Path to html files
    :type path: Path
    :return: None
    """

    # Create all the container urls
    for ct in containers.values():
        for c in ct.values():
            c.export_html()

    # Create an entry point
    html = HTML(None, path / "index.html")

    tab = html.add_tab("Projects")
    tab.embed_url("./projects/index.html")
    tab = html.add_tab("Resources")
    tab.embed_url("./resources/index.html")
    tab = html.add_tab("Milestones")
    tab.embed_url("./milestones/index.html")

    html.export()

__all__ = [
    "__version__",
    "import_from_yaml",
    "create_containers",
    "export_to_html",
]
