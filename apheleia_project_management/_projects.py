import pandas as pd
from pathlib import Path

from ._containers import Container, containers
from ._charts import gantt
from ._utils import today
from ._workpackages import create_allocation_chart

class Project(Container):
    def __init__(self, name: str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("project", name, path)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        df = pd.DataFrame(columns=["project", "start", "end", "description"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        # Add availability gantt
        tab = self.html.add_tab("Timeline")
        tab.add_chart("Project Timeline", gantt(
                                                df,
                                                "",
                                                ("start", "Start Date"),
                                                ("end", "End Date"),
                                                ("project", "Project Name"),
                                                markers={"Today" : today},
                                            )
        )

        # Find all workpackages relating to this projects
        workpackages = []
        for k,v in containers["workpackage"].items():
            if not v.summary_df[v.summary_df["project"] == self.name].empty:
                workpackages.append(v)

        try:
            wp_summary_df = pd.concat([v.summary_df for v in workpackages], ignore_index=True)
            wp_raw_df = pd.concat([v.imported_df for v in workpackages], ignore_index=True)

            tab = self.html.add_tab("Workpackages")
            tab.add_chart("Workpackage Timeline", gantt(
                                                    wp_summary_df,
                                                    "",
                                                    ("start", "Start Date"),
                                                    ("end", "End Date"),
                                                    ("workpackage", "Workpackage Name"),
                                                    markers={"Today" : today},
                                                )
            )
            tab.add_chart("Workpackage Allocations", create_allocation_chart(wp_raw_df, "allocations.resource"))
            tab.add_table("Workpackages", wp_summary_df)
        except:
            pass

        # Add details table
        tab = self.html.add_tab("Details")
        tab.add_table("", df, transpose=True)

        super().export_html()

class Projects(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("projects", name, path)

    def import_data(self, l : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param l: List of dictionaries
        :return: None
        """

        super().import_data(l)

        # Create child projects
        for p in l:
            name = p["project"]
            if name not in self.children:
                self.children[name] = Project(name, self.path)
                self.children[name].import_data([p])
            else:
                raise ValueError(f"Project {name} already exists")

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Summary Table
        df = pd.DataFrame(columns=["project", "start", "end", "description"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        # Add Timeline to html
        tab = self.html.add_tab("Timelines")
        tab.add_chart("Project Timelines", gantt(
                                                        df,
                                                        "",
                                                        ("start", "Start Date"),
                                                        ("end", "End Date"),
                                                        ("project", "Project Name"),
                                                        markers={"Today" : today},
                                                    )
        )

        # Add table to html
        tab = self.html.add_tab("Projects")
        tab.add_table("Projects", df)

        super().export_html()

__all__ = [
    "Project",
    "Projects",
]
