import os
import urllib.parse
from pathlib import Path

import pandas as pd

from ._charts import gantt
from ._containers import Container, containers
from ._tasks import milestone_task_summary, tasks_over_estimate
from ._utils import milestone_badges, smart_date_converter, today
from ._workpackages import MILESTONE_HELP, check_milestones, create_allocation_chart, workpackages_outside_milestone


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

        # Summary Table
        #   - remove milestones
        df = pd.DataFrame(columns=["project", "start", "end", "description"])
        df = pd.concat([self.imported_df, df], ignore_index=True)
        if "milestones" in df.columns:
            df = df.drop(columns=["milestones"]).drop_duplicates()
            df = df.reset_index(drop=True)

        # Get milestones
        milestones_df = None
        markers = {"Today" : today}
        if "milestones" in self.imported_df.columns:
            given = pd.json_normalize([m for m in self.imported_df["milestones"] if isinstance(m, dict)])
            index = containers.get("milestones", {}).get("index")
            defined = index.imported_df if index is not None and index.imported_df is not None else pd.DataFrame(columns=["milestone"])
            if not given.empty and "milestone" in given.columns:
                milestones_df = pd.merge(given, defined, on='milestone', how='inner')
                milestones_df["date"] = milestones_df["date"].apply(smart_date_converter)
                markers = markers | milestones_df.set_index('milestone')['date'].to_dict()
                if milestones_df.empty:
                    milestones_df = None

        # Summary: description, then the status of the project's tasks by milestone
        tab = self.html.add_tab("Summary")
        description = self.imported_df["description"].dropna() if "description" in self.imported_df.columns else []
        tab.add_paragraph("Description", description.iloc[0] if len(description) > 0 else "No description has been provided for this project.",
                          help="Description of the project, as given in the projects input file.")

        tasks_index = containers.get("tasks", {}).get("index")
        project_tasks = None
        if tasks_index is not None and tasks_index.imported_df is not None and "project" in tasks_index.imported_df.columns:
            project_tasks = tasks_index.imported_df[tasks_index.imported_df["project"] == self.name]

        if project_tasks is not None and not project_tasks.empty:
            tasks_page = containers["tasks"]["index"].html.path
            href = os.path.relpath(tasks_page, self.html.path.parent).replace(os.sep, "/") + "#project=" + urllib.parse.quote(self.name)

            tab.add_table("Task Status by Milestone", milestone_task_summary(project_tasks, milestones_df, tasks_href=href),
                          help="Status of all of this project's tasks, grouped by the milestone they are needed for. A task "
                               "belongs to the first milestone dated on or after its forecast finish. The highlighted row is "
                               "the current milestone: the next one due. Click a task count to open the tasks page filtered "
                               "to this project. Spent and remaining are in days. Over estimate flags milestones with tasks "
                               "whose spent plus remaining effort is more than their estimate.")

            over = tasks_over_estimate(project_tasks)
            if over.empty:
                tab.add_paragraph("Tasks Past Estimate", "No tasks are past their estimate.",
                                  help="Tasks whose spent plus remaining effort is more than their estimate.")
            else:
                tab.add_table("Tasks Past Estimate", over,
                              help="Tasks whose spent plus remaining effort is now more than their estimate, worst first. "
                                   "Over by is the number of days past the estimate. Tasks with no estimate cannot be "
                                   "checked and are not listed.")
        else:
            tab.add_paragraph("Task Status by Milestone", "No tasks have been recorded for this project.")

        # Workpackages outside their milestone
        wp_all = [v.summary_df for v in containers.get("workpackage", {}).values() if (v.summary_df["project"] == self.name).any()]
        if wp_all:
            wp_df = pd.concat(wp_all, ignore_index=True)
            wp_df = wp_df[wp_df["project"] == self.name]
            outside = workpackages_outside_milestone(wp_df)
            if outside.empty:
                tab.add_paragraph("Workpackages Outside Milestone", "All workpackages with a milestone fall within its range.",
                                  help=MILESTONE_HELP)
            else:
                tab.add_table("Workpackages Outside Milestone", outside, help=MILESTONE_HELP)

        # Add Timeline gantt
        tab = self.html.add_tab("Timeline")
        tab.add_chart("Project Timeline", gantt(
                                                df,
                                                "",
                                                ("start", "Start Date"),
                                                ("end", "End Date"),
                                                ("project", "Project Name"),
                                                markers=markers,
                                                description="description",
                                                link_key="project",
                                            )
        )
        # Milestones table
        if milestones_df is not None:
            milestones_df = milestones_df.sort_values("date").reset_index(drop=True)
            milestones_df["when"] = milestone_badges(milestones_df["date"])
            tab.add_table("Milestones", milestones_df,
                          help="This project's milestones and their dates. The current milestone is the next one due.")

        # Find all workpackages relating to this projects
        workpackages = []
        for v in containers.get("workpackage", {}).values():
            if not v.summary_df[v.summary_df["project"] == self.name].empty:
                workpackages.append(v)

        if workpackages:
            wp_summary_df = pd.concat([v.summary_df for v in workpackages], ignore_index=True)
            wp_raw_df = pd.concat([v.imported_df for v in workpackages], ignore_index=True)

            tab = self.html.add_tab("Workpackages")
            tab.add_chart("Workpackage Timeline", gantt(
                                                    check_milestones(wp_summary_df),
                                                    "",
                                                    ("start", "Start Date"),
                                                    ("end", "End Date"),
                                                    ("workpackage", "Workpackage Name"),
                                                    markers={"Today" : today},
                                                    description="description",
                                                    link_key="workpackage",
                                                    milestones=("milestone", "milestone date"),
                                                )
            )
            tab.add_chart("Workpackage Allocations", create_allocation_chart(wp_raw_df, "allocations.resource"))
            tab.add_table("Workpackages", check_milestones(wp_summary_df), help=MILESTONE_HELP)

        # Add details table
        tab = self.html.add_tab("Details")
        tab.add_table("Project Details", df, transpose=True, help="Definition of this project as given in the projects input file.")

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

    def import_data(self, definitions : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param definitions: List of dictionaries
        :return: None
        """

        self.check_definitions(definitions, "project")
        super().import_data(definitions)
        self.validate_data(self.imported_df, pd.DataFrame(columns=["project", "start", "end", "description", "milestones"]))

        # Create child projects
        for p in definitions:
            name = p["project"]
            self.children[name] = Project(name, self.path)
            self.children[name].import_data([p])

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Summary Table
        #   - remove milestones
        df = pd.DataFrame(columns=["project", "start", "end", "description"])
        df = pd.concat([self.imported_df, df], ignore_index=True)
        if "milestones" in df.columns:
            df = df.drop(columns=["milestones"]).drop_duplicates()
            df = df.reset_index(drop=True)

        if df.empty:
            tab = self.html.add_tab("Projects")
            tab.add_paragraph("Projects", "No projects have been defined.")
            super().export_html()
            return

        # Add Timeline to html
        tab = self.html.add_tab("Timelines")
        tab.add_chart("Project Timelines", gantt(
                                                        df,
                                                        "",
                                                        ("start", "Start Date"),
                                                        ("end", "End Date"),
                                                        ("project", "Project Name"),
                                                        markers={"Today" : today},
                                                        description="description",
                                                        link_key="project",
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
