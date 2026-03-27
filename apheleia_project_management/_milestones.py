import pandas as pd
from pathlib import Path
from ._containers import Container

class Milestone(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("milestone", name, path)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Summary Table
        df = pd.DataFrame(columns=["milestone", "description"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        # Add to html
        tab = self.html.add_tab("Details")
        tab.add_table("", df, transpose=True)

        super().export_html()

class Milestones(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("milestones", name, path)

    def import_data(self, l : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param l: List of dictionaries
        :return: None
        """

        super().import_data(l)

        # Create child projects
        for p in l:
            name = p["milestone"]
            if name not in self.children:
                self.children[name] = Milestone(name, self.path)
                self.children[name].import_data([p])
            else:
                raise ValueError(f"milestone {name} already exists")

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Summary Table
        df = pd.DataFrame(columns=["milestone", "description"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        # Add to html
        tab = self.html.add_tab("Milestones")
        tab.add_table("Milestones", df)

        super().export_html()

__all__ = [
    "Milestones"
]
