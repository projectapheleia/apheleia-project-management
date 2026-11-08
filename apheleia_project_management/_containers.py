from pathlib import Path

import pandas as pd

from ._html import HTML
from ._utils import value_to_filename

containers = {}
""" Global handle to all containers """

class Container:

    def __init__(self, container_type : str, name : str, path : Path) -> None:
        """
        Constructor
        """

        self.container_type = container_type
        """ Container type """

        self.name = name
        """ Container name / identifier """

        self.path = path
        """ Path to container """

        self.imported_df = None
        """ Dataframe containing all imported data """

        self.html = HTML(self, path / f"{value_to_filename(self.name)}.html")
        """ HTML class """

        self.children = {}
        """ Children containers"""

        # Register container with global handle
        if self.container_type not in containers:
            containers[container_type] = {}
        containers[container_type][name] = self

    def import_data(self, definitions : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param definitions: List of dictionaries
        :return: None
        """

        # Convert new data to dataframe
        self.imported_df = pd.DataFrame(definitions)

        # Columns with lists
        columns_with_lists = [
            col for col in self.imported_df.columns if self.imported_df[col].dropna().apply(lambda x: isinstance(x, list)).any()
        ]

        for col in columns_with_lists:
            self.imported_df = self.imported_df.explode(col)

    def check_definitions(self, definitions : list[dict], key : str) -> None:
        """
        Check every definition has a name, and that no name is defined more than once

        :param definitions: List of definitions
        :type definitions: list[dict]
        :param key: Field holding the name of each definition, e.g. "task"
        :type key: str
        :return: None
        """

        seen = set()
        for d in definitions:
            name = d.get(key)
            if name is None or str(name).strip() == "":
                raise ValueError(f"{key} definition has no {key} name: {d}")
            if name in seen:
                raise ValueError(f"{key} {name} is defined more than once")
            seen.add(name)

    def validate_data(self, df : pd.DataFrame, ref_df : pd.DataFrame) -> None:
        """
        Validate data against a reference dataframe

        :param df: Dataframe to validate
        :type df: pd.DataFrame
        :param ref_df: Reference dataframe. Its first column is the name of each definition
        :type ref_df: pd.DataFrame
        :return: None
        """

        unexpected = sorted(set(df.columns) - set(ref_df.columns))
        if unexpected:
            key = ref_df.columns[0]
            where = []
            if key in df.columns:
                for col in unexpected:
                    names = df.loc[df[col].notna(), key].drop_duplicates().astype(str).tolist()
                    where.append(f"{col!r} in {', '.join(names)}")
            expected = ", ".join(c.split(".")[-1] if "." in c else c for c in ref_df.columns)
            raise ValueError(f"{self.container_type} definitions contain unexpected fields: "
                             f"{'; '.join(where) if where else ', '.join(unexpected)}. Expected fields are: {expected}")

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        self.html.export()

__all__ = [
    "Container",
]
