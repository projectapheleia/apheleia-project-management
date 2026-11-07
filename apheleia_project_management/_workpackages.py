from pathlib import Path

import pandas as pd
import plotly.express as px

from ._charts import SCALES, aggregate_by_period, color_map, gantt, stacked_bar
from ._containers import Container, containers
from ._tasks import (
    MISSING,
    create_task_progress_by_task,
    create_task_timeline,
    project_milestones,
    task_summary_stats,
    task_summary_table,
)
from ._utils import smart_date_converter, today

OUTSIDE = '<span class="badge badge-missing">OUTSIDE MILESTONE</span>'
""" Shown against a workpackage whose dates do not fall within its milestone """

WITHIN = '<span class="badge badge-upcoming">Within milestone</span>'
""" Shown against a workpackage whose dates fall within its milestone """

MILESTONE_HELP = ("Milestone is the milestone the workpackage is working towards. The workpackage must end by the date of "
                  "this milestone, to the month; starting earlier is fine. Workpackages that end after their milestone, or "
                  "whose milestone has no date in the project, are marked OUTSIDE MILESTONE.")
""" Hover guidance for the milestone columns """


class Workpackage(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("workpackage", name, path)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """
        wp_start = self.summary_df['start'].min()
        wp_end = self.summary_df['end'].max()

        # Add Timeline to html
        tab = self.html.add_tab("Timelines")
        tab.add_chart("Workpackage Timelines", gantt(
                                                        check_milestones(self.summary_df),
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

        # Milestone
        checked = check_milestones(self.summary_df)
        if checked["milestone"].notna().any():
            tab.add_table("Milestone", checked[["workpackage", "milestone", "milestone range", "milestone check"]]
                          .rename(columns={"milestone check" : "check"}), help=MILESTONE_HELP)

        # Add Resource allocation stacked bar to html
        tab = self.html.add_tab("Allocations")
        tab.add_chart("Workpackage Allocations", create_allocation_chart(self.imported_df, "allocations.resource"))

        # Tasks
        # Find all tasks relating to this workpackage
        tasks = []
        for v in containers.get("tasks", {}).values():
            if v.imported_df is not None and "workpackage" in v.imported_df.columns and \
               not v.imported_df[v.imported_df["workpackage"] == self.name].empty:
                tasks.append(v)

        if len(tasks) != 0:
            tasks_df = pd.concat([v.imported_df for v in tasks], ignore_index=True)
            tasks_df = tasks_df[tasks_df["workpackage"] == self.name]

            tab = self.html.add_tab("Tasks")

            # Overall summary
            tab.add_summary("Task Progress Summary", task_summary_stats(tasks_df),
                            help="Overall progress of every task in this workpackage. Overall progress is the effort spent "
                                 "as a percentage of effort spent plus remaining. Forecast finish is the latest forecast "
                                 "completion of any task.")

            # Progress of each task
            tab.add_chart("Progress by Task", create_task_progress_by_task(tasks_df),
                          help="One bar per task in this workpackage. The first part is effort spent, the rest is effort "
                               "remaining (days), so the full length is the current estimate for the task. "
                               "Blue is effort within the original estimate (the black line), red is effort past it, so a late task ends in red. "
                               "Click a bar to open the task page.")

            # Timeline
            tab.add_chart("Task Timeline", create_task_timeline(tasks_df,
                                                                markers={
                                                                            "Today" : today,
                                                                            "Workpackage Start" : wp_start,
                                                                            "Workpackage End" : wp_end,
                                                                        }
                                                                )
                        )

            # Summary Table
            tab.add_table("Tasks", task_summary_table(tasks_df),
                          help="Progress of every task in this workpackage. Spent and remaining are in days; "
                               "remaining of 0 means the task is complete.")

        super().export_html()

class WorkPackages(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("workpackages", name, path)

    def import_data(self, definitions : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param definitions: List of dictionaries
        :return: None
        """

        columns=[
                    "workpackage",
                    "project",
                    "allocations.start",
                    "allocations.end",
                    "allocations.resource",
                    "allocations.allocation",
                    "description",
                    "milestone"
                ]

        self.check_definitions(definitions, "workpackage")

        # No workpackages defined
        if not definitions:
            self.imported_df = pd.DataFrame(columns=columns)
            self.summary_df = pd.DataFrame(columns=["workpackage", "project", "start", "end", "resources", "effort", "description", "milestone"])
            return

        # Every workpackage needs at least one allocation
        for d in definitions:
            if not d.get("allocations"):
                raise ValueError(f"workpackage {d.get('workpackage')} has no allocations")

        all_top_level_keys = {key for d in definitions for key in d.keys()}
        meta_cols = [k for k in all_top_level_keys if k != "allocations"]

        # Convert new data to dataframe
        self.imported_df = pd.json_normalize(
                                                definitions,
                                                record_path=["allocations"],
                                                meta=meta_cols,
                                                record_prefix="allocations.",
                                                errors="ignore"
        )

        # Columns with lists
        columns_with_lists = [
            col for col in self.imported_df.columns if self.imported_df[col].dropna().apply(lambda x: isinstance(x, list)).any()
        ]

        for col in columns_with_lists:
            self.imported_df = self.imported_df.explode(col)

        # Create a summary dataframe
        df = pd.DataFrame(columns=columns)
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)
        df = df[columns]
        self.summary_df = summarize_df(df)

        # Create child projects
        for p in definitions:
            name = p["workpackage"]
            self.children[name] = Workpackage(name, self.path)
            self.children[name].imported_df = self.imported_df[self.imported_df["workpackage"] == name]
            self.children[name].summary_df = self.summary_df[self.summary_df["workpackage"] == name]

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        if self.summary_df.empty:
            tab = self.html.add_tab("Workpackages")
            tab.add_paragraph("Workpackages", "No workpackages have been defined.")
            super().export_html()
            return

        # Add Timeline to html
        tab = self.html.add_tab("Timelines")
        tab.add_chart("Workpackage Timelines", gantt(
                                                        check_milestones(self.summary_df),
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

        # Add Resource allocation stacked bar to html
        tab = self.html.add_tab("Allocations")
        tab.add_chart("Workpackage Allocations", create_allocation_chart(self.imported_df, "workpackage"))

        # Add table to html
        tab = self.html.add_tab("Workpackages")
        tab.add_table("Workpackages", check_milestones(self.summary_df), help=MILESTONE_HELP)

        super().export_html()

def check_milestones(summary_df : pd.DataFrame) -> pd.DataFrame:
    """
    Check each workpackage falls within the range of its milestone

    A workpackage must end by the date of its milestone; starting early is fine. Allocations are
    in whole months so the comparison is made to the month.
    A workpackage with a milestone that the project has not dated cannot be checked and is
    also flagged. Workpackages with no milestone are not checked.

    :param summary_df: One row per workpackage, with project, start, end and milestone columns
    :type summary_df: pd.DataFrame
    :return: Copy of the dataframe with milestone range, milestone check (html) and outside (bool) and milestone date columns
    :rtype: pd.DataFrame
    """

    df = summary_df.copy()
    ranges, checks, outside, dates = [], [], [], []

    for r in df.itertuples():
        milestone = getattr(r, "milestone", None)
        if not isinstance(milestone, str) or milestone.strip() == "":
            ranges.append("")
            checks.append("")
            outside.append(False)
            dates.append(pd.NaT)
            continue

        ms = project_milestones(r.project)
        due = ms[ms["milestone"] == milestone]
        if due.empty:
            ranges.append(MISSING)
            checks.append(f"{OUTSIDE} {milestone} has no date in {r.project}")
            outside.append(True)
            dates.append(pd.NaT)
            continue

        end = due["date"].iloc[0]
        ranges.append(f"by {end.date()}")
        dates.append(end)

        problems = []
        if pd.notna(r.end) and r.end.to_period("M") > end.to_period("M"):
            problems.append(f"ends {r.end:%Y-%m}, after {milestone} ({end:%Y-%m})")

        checks.append(f"{OUTSIDE} {'; '.join(problems)}" if problems else WITHIN)
        outside.append(bool(problems))

    df["milestone range"] = ranges
    df["milestone check"] = checks
    df["outside"] = outside
    df["milestone date"] = pd.to_datetime(pd.Series(dates, index=df.index))
    return df

def workpackages_outside_milestone(summary_df : pd.DataFrame) -> pd.DataFrame:
    """
    The workpackages that fall outside the range of their milestone

    :param summary_df: One row per workpackage
    :type summary_df: pd.DataFrame
    :return: Workpackage, milestone, milestone range, start, end and the reason it is outside
    :rtype: pd.DataFrame
    """

    df = check_milestones(summary_df)
    df = df[df["outside"]]
    df = df[["workpackage", "milestone", "milestone range", "start", "end", "milestone check"]]
    return df.rename(columns={"milestone check" : "problem"}).reset_index(drop=True)

def summarize_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    Create a summarized dataframe

    :param df: Dataframe to summarize
    :type df: pd.DataFrame
    :return: pd.DataFrame
    :rtype: pd.DataFrame
    """

    # Define the aggregation rules
    agg_rules = {
        'allocations.start': 'min',
        'allocations.end': 'max',
        'allocations.resource': lambda x: list(set(x)),
        'allocations.allocation': 'sum',
        'description': 'first',
        'milestone': 'first'
    }

    # Group and apply
    df_reduced = df.groupby(['workpackage', 'project'], as_index=False).agg(agg_rules)

    # Rename columns to your desired output names
    df_reduced = df_reduced.rename(columns={
        'allocations.start': 'start',
        'allocations.end': 'end',
        'allocations.resource': 'resources',
        'allocations.allocation': 'effort'
    })
    df_reduced["start"] = df_reduced["start"].apply(smart_date_converter)
    df_reduced["end"] = df_reduced["end"].apply(smart_date_converter)

    return df_reduced

def create_allocation_chart(df : pd.DataFrame, groupby : str) -> px.bar:
    """
    Create a stacked bar for allocations

    :param df: Dataframe to create chart from
    :type df: pd.DataFrame
    :return: px.bar
    :rtype: px.bar
    """

    # Function to return a list of month starts and ends
    def get_month_range(row):
        # 1. Convert to Timestamp if they aren't already
        start_dt = pd.to_datetime(row['allocations.start'])
        end_dt = pd.to_datetime(row['allocations.end'])

        # 2. Subtract 2 months from start, add 2 months to end
        # We use MonthBegin (MS) to ensure we hit the start of those padded months
        padded_start = start_dt - pd.DateOffset(months=2)
        padded_end = end_dt + pd.DateOffset(months=2)

        return pd.date_range(
            start=padded_start,
            end=padded_end,
            freq='MS',
            inclusive='both'
        )

    # Create a month column and explode it based on allocation start-end
    df = df.copy()
    df['month'] = df.apply(get_month_range, axis=1)
    df_monthly = df.explode('month')

    # Zero out values not within range
    mask = (df_monthly['month'] < pd.to_datetime(df_monthly['allocations.start'])) | (df_monthly['month'] > pd.to_datetime(df_monthly['allocations.end']))
    df_monthly.loc[mask, 'allocations.allocation'] = 0

    # Group by month and name to ensure overlapping entries are summed
    df_plot = df_monthly.groupby(['month', groupby], as_index=False)['allocations.allocation'].sum()

    # Hover text for each group
    descriptions = {}
    if "description" in df.columns and groupby == "workpackage":
        descriptions = df.groupby(groupby)["description"].first().fillna("").to_dict()

    # Same colour for the same name everywhere. Resources use the order of the resources page
    names = list(df_plot[groupby].unique())
    if groupby == "allocations.resource":
        index = containers.get("resources", {}).get("index")
        if index is not None and index.imported_df is not None:
            names = list(index.imported_df["resource"]) + names
    colors = color_map(names)

    # One chart per time scale. Effort is added up over each period
    figs = {}
    for scale, (_, x_label, tick_format, hover_format) in SCALES.items():
        figs[scale] = stacked_bar(
            aggregate_by_period(df_plot, "month", [groupby], "allocations.allocation", scale, "sum"),
            "",
            ("month", x_label),
            ("allocations.allocation", "Allocation (Months Effort)"),
            groupby,
            height=1000,
            bar_width={"Monthly" : 50, "Quarterly" : 80, "Yearly" : 120}[scale],
            descriptions=descriptions,
            link_key={"workpackage" : "workpackage", "project" : "project"}.get(groupby, "resource"),
            tickformat=tick_format,
            hover_date_format=hover_format,
            colors=colors,
        )

    return figs

__all__ = [
    "Workpackage",
    "WorkPackages",
    "summarize_df",
    "check_milestones",
    "workpackages_outside_milestone",
    "create_allocation_chart",
]
