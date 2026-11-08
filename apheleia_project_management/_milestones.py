import html as _html
import os
from pathlib import Path

import pandas as pd

from ._containers import Container, containers
from ._tasks import project_milestones
from ._utils import milestone_badges


def milestone_dates() -> pd.DataFrame:
    """
    Every date given to a milestone by a project, with whether it is that project's current milestone

    :return: Dataframe with project, milestone, start, end and when (html badge) columns. The end is the
             date the milestone is due; the start is blank for a milestone on a single date
    :rtype: pd.DataFrame
    """

    frames = []
    for name in containers.get("project", {}):
        ms = project_milestones(name)
        if ms.empty:
            continue
        ms = ms.assign(project=name)
        ms["when"] = milestone_badges(ms["date"])
        frames.append(ms)

    if not frames:
        return pd.DataFrame(columns=["project", "milestone", "start", "end", "when"])
    out = pd.concat(frames, ignore_index=True).rename(columns={"date" : "end"})
    return out[["project", "milestone", "start", "end", "when"]]

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
        dates = milestone_dates()
        dates = dates[dates["milestone"] == self.name].drop(columns=["milestone"]).sort_values("end")
        if not dates.empty:
            tab = self.html.add_tab("Projects")
            tab.add_table("Projects Using This Milestone", dates.reset_index(drop=True),
                          help="The projects that have given this milestone a date. A milestone on a single date has only "
                               "an end date. The current milestone for a project is the next one due.")

        tab = self.html.add_tab("Details")
        tab.add_table("Milestone Details", df, transpose=True, help="Definition of this milestone as given in the milestones input file.")

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

    def import_data(self, definitions : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param definitions: List of dictionaries
        :return: None
        """

        self.check_definitions(definitions, "milestone")
        super().import_data(definitions)
        if self.imported_df.empty:
            self.imported_df = pd.DataFrame(columns=["milestone", "description"])
        self.validate_data(self.imported_df, pd.DataFrame(columns=["milestone", "description"]))

        # Create child milestones
        for p in definitions:
            name = p["milestone"]
            self.children[name] = Milestone(name, self.path)
            self.children[name].import_data([p])

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Summary Table
        df = pd.DataFrame(columns=["milestone", "description"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        # A milestone is current for each project in which it is the next one due
        dates = milestone_dates()
        current_for, next_due = [], []
        for m in df["milestone"]:
            d = dates[dates["milestone"] == m]
            cur = d[d["when"].str.contains("badge-current")]
            links = [f'<a href="{_html.escape(os.path.relpath(containers["project"][p].html.path, self.html.path.parent).replace(os.sep, "/"))}">'
                     f'{_html.escape(p)}</a>' for p in cur["project"] if p in containers.get("project", {})]
            current_for.append(", ".join(links))
            next_due.append(cur["end"].min() if not cur.empty else pd.NaT)

        df = df.copy()
        df["when"] = ['<span class="badge badge-current">&#9679; Current milestone</span>' if c else "" for c in current_for]
        df["current for"] = current_for
        df["next due"] = next_due

        # Add to html
        tab = self.html.add_tab("Milestones")
        if df.empty:
            tab.add_paragraph("Milestones", "No milestones have been defined.")
            super().export_html()
            return
        tab.add_table("Milestones", df,
                      help="All milestones. A milestone is current for a project when it is the next one due in that project; "
                           "the projects it is current for are listed, with the earliest date.")

        super().export_html()

__all__ = [
    "Milestones"
]
