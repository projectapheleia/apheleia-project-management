import pandas as pd
from pathlib import Path
from ._html import HTML
from ._utils import value_to_filename

containers = {}
""" Global handle to all containers """

class Container():

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

        if not self.path.exists():
            self.path.mkdir(parents=True)

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

    def import_data(self, l : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param l: List of dictionaries
        :return: None
        """

        # Convert new data to dataframe
        self.imported_df = pd.DataFrame(l)

        # Columns with lists
        columns_with_lists = [
            col for col in self.imported_df.columns if self.imported_df[col].dropna().apply(lambda x: isinstance(x, list)).any()
        ]

        for col in columns_with_lists:
            self.imported_df = self.imported_df.explode(col)

    def validate_data(self, df : pd.DataFrame, ref_df : pd.DataFrame) -> None:
        """
        Validate data against a reference dataframe

        :param df: Dataframe to validate
        :type df: pd.DataFrame
        :param ref_df: Reference dataframe
        :type ref_df: pd.DataFrame
        :return: None
        """

        if not set(df.columns).issubset(ref_df.columns):
            unexpected = set(df.columns) - set(ref_df.columns)
            raise ValueError(f" {self.name} data import failed: unexpected columns {unexpected}")

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        self.html.export()

__all__ = [
    "Container",
]
