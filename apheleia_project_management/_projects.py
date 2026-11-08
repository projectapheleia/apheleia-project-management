import os
import re
import urllib.parse
from pathlib import Path

import pandas as pd

from ._burn import add_burnchart, workpackage_allocation
from ._charts import gantt
from ._containers import Container, containers
from ._resources import add_over_allocation
from ._tasks import TASK_ESTIMATE_HELP, add_over_estimate, milestone_task_summary
from ._utils import milestone_badges, milestone_dates_text, smart_date_converter, today_markers
from ._workpackages import (
    ESTIMATE_HELP,
    MILESTONE_HELP,
    TASK_EFFORT_HELP,
    check_milestones,
    create_allocation_chart,
    task_effort_table,
    workpackage_table,
    workpackages_outside_milestone,
    workpackages_over_estimate,
    workpackages_over_task_effort,
)

DATE_FIELDS = ("date", "start", "end")
""" Fields of a project milestone that hold dates """

RELATIVE_DATE = re.compile(r"\s*(?:(?P<ms>.+?)\.)?(?P<field>date|start|end)"
                           r"(?:\s*(?P<sign>[+-])\s*(?P<n>\d+)\s*(?P<unit>day|week|month|year)s?)?\s*")
""" A date relative to a milestone of the project, e.g. M1.start + 6 months """

def resolve_milestone_dates(project : dict) -> None:
    """
    Check the milestones of a project definition and replace relative dates with YYYY-MM-DD, in place.

    A milestone has a date, or a start and an end. Any of these can be relative to a milestone of the
    same project, e.g. "M1.start + 6 months", or to the milestone's own fields, e.g. "start + 7 weeks".
    When referenced, date and end are both the date a milestone is due, and the start of a single date
    milestone is its date.

    :param project: Project definition
    :type project: dict
    :return: None
    """

    milestones = [m for m in project.get("milestones") or [] if isinstance(m, dict)]
    names = set()
    raw = {}
    for m in milestones:
        name = m.get("milestone")
        where = f"milestone {name} of project {project['project']}"
        if name in names:
            raise ValueError(f"{where} is given more than once")
        names.add(name)
        unexpected = sorted(set(m) - {"milestone", *DATE_FIELDS})
        if unexpected:
            raise ValueError(f"{where} has unexpected fields: {', '.join(unexpected)}. "
                             f"Expected fields are: milestone, date or start and end")
        for k in DATE_FIELDS:
            v = smart_date_converter(m.get(k))
            if isinstance(v, str):
                raw[(name, k)] = RELATIVE_DATE.fullmatch(v)
                if raw[(name, k)] is None:
                    raise ValueError(f"{where} has {k} {v!r}, which is not a date or a relative date such as 'M1.start + 6 months'")
            elif v is not None and pd.notna(v):
                raw[(name, k)] = pd.Timestamp(v)
        given = {k for k in DATE_FIELDS if (name, k) in raw}
        if given and given != {"date"} and given != {"start", "end"}:
            raise ValueError(f"{where} must have either a date, or both a start and an end date")

    resolved = {}

    def resolve(key, chain=()):
        # Date of a (milestone, field), following relative dates. Chain is the keys being resolved, to catch loops
        if key in resolved:
            return resolved[key]
        value = raw[key]
        if isinstance(value, re.Match):
            where = f"milestone {key[0]} of project {project['project']}"
            if key in chain:
                raise ValueError(f"{where} has a {key[1]} that depends on itself")
            ref = value["ms"] or key[0]
            if ref not in names:
                raise ValueError(f"{where} refers to {ref}, which is not a milestone of the project")
            field = "start" if value["field"] == "start" else "end"
            ref_key = next((k for k in ((ref, field), (ref, "date")) if k in raw), None)
            if ref_key is None:
                raise ValueError(f"{where} refers to {ref}.{value['field']}, which has no date")
            date = resolve(ref_key, (*chain, key))
            if value["unit"]:
                n = int(value["n"]) * (-1 if value["sign"] == "-" else 1)
                date += pd.DateOffset(**{f"{value['unit']}s" : n})
            value = date
        resolved[key] = value
        return value

    for (name, k) in raw:
        resolve((name, k))
    for m in milestones:
        name = m.get("milestone")
        for k in DATE_FIELDS:
            if (name, k) in resolved:
                m[k] = f"{resolved[(name, k)]:%Y-%m-%d}"
        if (name, "start") in resolved and resolved[(name, "end")] < resolved[(name, "start")]:
            raise ValueError(f"milestone {name} of project {project['project']} ends ({m['end']}) before it starts ({m['start']})")


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
        markers = today_markers()
        windows = {}
        if "milestones" in self.imported_df.columns:
            given = pd.json_normalize([m for m in self.imported_df["milestones"] if isinstance(m, dict)])
            index = containers.get("milestones", {}).get("index")
            defined = index.imported_df if index is not None and index.imported_df is not None else pd.DataFrame(columns=["milestone"])
            if not given.empty and "milestone" in given.columns:
                milestones_df = pd.merge(given, defined, on='milestone', how='inner')
                for col in ("date", "start", "end"):
                    milestones_df[col] = pd.to_datetime(milestones_df[col], errors="coerce") if col in milestones_df else pd.NaT

                # A single date is a marker; a start and end is a window, due on its end date
                milestones_df["date"] = milestones_df.pop("end").fillna(milestones_df["date"])
                is_window = milestones_df["start"].notna()
                windows = {r.milestone : (r.start, r.date) for r in milestones_df[is_window].itertuples()}
                markers |= milestones_df[~is_window].set_index("milestone")["date"].to_dict()
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

            tab.add_table("Task Status by Milestone", milestone_task_summary(project_tasks, milestones_df, tasks_href=href), units=True,
                          help="Status of all of this project's tasks, grouped by the milestone they are needed for. A task "
                               "belongs to the first milestone dated on or after its forecast finish. The highlighted row is "
                               "the current milestone: the next one due. Click a task count to open the tasks page filtered "
                               "to this project. Over estimate flags milestones with tasks whose spent plus remaining effort is "
                               "more than their estimate. " + TASK_ESTIMATE_HELP)

            add_over_estimate(tab, project_tasks)
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

            over = workpackages_over_estimate(wp_df)
            if over.empty:
                tab.add_paragraph("Workpackages Over Estimate", "No workpackages are allocated more effort than their estimate.",
                                  help=ESTIMATE_HELP)
            else:
                tab.add_table("Workpackages Over Estimate", over, help=ESTIMATE_HELP, units=True)

            over = workpackages_over_task_effort(wp_df)
            if over.empty:
                tab.add_paragraph("Workpackages Over Task Effort",
                                  "The tasks of every workpackage fit within its allocation and estimate.", help=TASK_EFFORT_HELP)
            else:
                tab.add_table("Workpackages Over Task Effort", over, help=TASK_EFFORT_HELP, units=True)

            # Resources of this project allocated more than they have available, to this and other projects
            add_over_allocation(tab, project=self.name)

        # Add Timeline gantt
        tab = self.html.add_tab("Timeline")
        tab.add_chart("Project Timeline", gantt(
                                                df,
                                                "",
                                                ("start", "Start Date"),
                                                ("end", "End Date"),
                                                ("project", "Project Name"),
                                                markers=markers,
                                                windows=windows,
                                                description="description",
                                                link_key="project",
                                            )
        )
        # Milestones table
        if milestones_df is not None:
            milestones_df = milestones_df.sort_values("date").reset_index(drop=True)
            milestones_df["when"] = milestone_badges(milestones_df["date"])
            shown = milestones_df.assign(date=milestone_dates_text(milestones_df["start"], milestones_df["date"])).drop(columns=["start"])
            tab.add_table("Milestones", shown,
                          help="This project's milestones and their dates. A milestone with a start and end date is shown as "
                               "start to end, and is due on its end date. The current milestone is the next one due.")

        # Burndown and burnup of the project's tasks
        tab = self.html.add_tab("Burnchart")
        has_tasks = project_tasks is not None and not project_tasks.empty
        end = pd.to_datetime(df["end"].iloc[0], errors="coerce") if "end" in df.columns and len(df) else pd.NaT
        allocations = {wp : workpackage_allocation([wp]) for wp in project_tasks["workpackage"].unique()} if has_tasks else {}
        add_burnchart(tab, project_tasks if has_tasks else None, allocations, "project",
                      deadline=("Project end", end) if pd.notna(end) else None)

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
                                                    markers=today_markers(),
                                                    description="description",
                                                    link_key="workpackage",
                                                    milestones=("milestone", "milestone date"),
                                                )
            )
            tab.add_chart("Workpackage Allocations", create_allocation_chart(wp_raw_df, "allocations.resource"))
            tab.add_table("Workpackages", workpackage_table(wp_summary_df), help=MILESTONE_HELP + " " + ESTIMATE_HELP, units=True)
            tab.add_table("Task Effort", task_effort_table(wp_summary_df), help=TASK_EFFORT_HELP, units=True)

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
        for p in definitions:
            resolve_milestone_dates(p)
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
                                                        markers=today_markers(),
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
