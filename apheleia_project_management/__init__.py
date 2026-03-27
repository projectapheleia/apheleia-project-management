
import yaml
from pathlib import Path

from ._utils import smart_date_converter
from ._containers import containers
from ._milestones import Milestones
from ._resources import Resources
from ._projects import Projects
from ._workpackages import WorkPackages

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
        "workpackages" : []
    }

    for file_path in path.rglob("*.yaml"):
        with open(file_path, "r") as f:
            content = yaml.safe_load(f)

            if not content or "type" not in content:
                continue

            for k in data.keys():
                if content["type"] == f"{k}_definitions":
                    for d in content["data"]:
                        data[k].append({_k : smart_date_converter(_v) for _k, _v in d.items()})

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

    # Create directory if needed
    if not path.exists():
        path.mkdir(parents=True)

    # Create container classes and import data
    for k,v in data.items():
        if k == "milestones":
            c = Milestones("index", path / k)
        elif k == "resources":
            c = Resources("index", path / k)
        elif k == "projects":
            c = Projects("index", path / k)
        elif k == "workpackages":
            c = WorkPackages("index", path / k)
        else:
            raise ValueError(f"Unknown container type: {k}")

        # Import data
        c.import_data(v)

def export_to_html():
    """
    Export all containers to html

    :return: None
    """

    for ct in containers.values():
        for c in ct.values():
            c.export_html()

__all__ = [
    "import_from_yaml",
    "create_containers",
    "export_to_html",
]
