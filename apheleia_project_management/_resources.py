import pandas as pd
from pathlib import Path

from ._containers import Container
from ._charts import gantt
from ._utils import today

class Resource(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("resource", name, path)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        df = pd.DataFrame(columns=["resource", "uname", "start", "end", "profile"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        # Add availability gantt
        tab = self.html.add_tab("Availability")
        tab.add_chart("Availability", gantt(
                                                df,
                                                "",
                                                ("start", "Start Date"),
                                                ("end", "End Date"),
                                                ("resource", "Resource Name"),
                                                markers={"Today" : today},
                                            )
        )

        # Add details table
        tab = self.html.add_tab("Details")
        tab.add_table("", df, transpose=True)

        super().export_html()

class Resources(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("resources", name, path)

    def import_data(self, l : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param l: List of dictionaries
        :return: None
        """

        super().import_data(l)

        # Create child projects
        for p in l:
            name = p["resource"]
            if name not in self.children:
                self.children[name] = Resource(name, self.path)
                self.children[name].import_data([p])
            else:
                raise ValueError(f"milestone {name} already exists")

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Summary Table
        df = pd.DataFrame(columns=["resource", "uname", "start", "end", "profile"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        # Add Gantt to html
        tab = self.html.add_tab("Availability")
        tab.add_chart("Resource Availability", gantt(
                                                        df,
                                                        "",
                                                        ("start", "Start Date"),
                                                        ("end", "End Date"),
                                                        ("resource", "Resource Name"),
                                                        markers={"Today" : today},
                                                    )
        )

        # Add table to html
        tab = self.html.add_tab("Resources")
        tab.add_table("Resources", df)

        super().export_html()

__all__ = [
    "Resources",
]
