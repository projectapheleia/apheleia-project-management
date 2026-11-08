import html as _html
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import _format
from ._charts import BAR_WIDTH, EFFORT_COLORS, SCALES, _shade_bars, aggregate_by_period, gantt, stacked_bar, style_axes
from ._containers import Container, containers
from ._utils import (
    DAYS_PER_MONTH,
    format_days,
    milestone_badges,
    milestone_dates_text,
    parse_effort,
    smart_date_converter,
    today,
)


class Task(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("task", name, path)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """
        tab = self.html.add_tab("Summary")

        # Timeline
        tab.add_chart("Task Timeline", create_task_timeline(self.imported_df))

        # Summary Table
        tab.add_table("Latest Status", task_summary_table(self.imported_df), units=True,
                      help="The most recent status of this task. Start is the date given for the task, or the previous "
                           "milestone if none was given. MISSING means no estimate was provided. Variance is spent plus "
                           "remaining minus the estimate. Remaining of 0 means the task is complete. " + TASK_ESTIMATE_HELP)

        # Progress
        tab = self.html.add_tab("Progress")
        tab.add_summary("Task Progress Summary", task_summary_stats(self.imported_df),
                        help="Overall progress of this task. Progress is the effort spent as a percentage of effort "
                             "spent plus remaining. Forecast finish is the forecast completion date.")
        tab.add_chart("Task Progress", create_task_progress(self.imported_df, "task",
                                                            link_to=("workpackage", str(self.imported_df["workpackage"].iloc[0]))),
                      help="History of the task. Each bar is the effort spent plus the effort remaining at that date, so "
                           "the total height is the current estimate to complete. Click a bar to open the workpackage "
                           "the task belongs to.")

        super().export_html()

class Tasks(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("tasks", name, path)

    def import_data(self, definitions : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param definitions: List of dictionaries
        :return: None
        """

        columns=[
                    "task",
                    "project",
                    "workpackage",
                    "resource",
                    "status.date",
                    "status.spent",
                    "status.remaining",
                    "description",
                    "start",
                    "estimate"
                ]

        self.check_definitions(definitions, "task")

        # No tasks defined
        if not definitions:
            self.imported_df = pd.DataFrame(columns=columns + ["resources"])
            return

        # Effort in days, resources as a tuple, and every status update checked
        known = set(containers.get("resource", {}))
        definitions = [parse_task(d, known) for d in definitions]

        all_top_level_keys = {key for d in definitions for key in d.keys()}
        meta_cols = [k for k in all_top_level_keys if k != "status"]

        # Convert new data to dataframe
        self.imported_df = pd.json_normalize(
                                                definitions,
                                                record_path=["status"],
                                                meta=meta_cols,
                                                record_prefix="status.",
                                                errors="ignore"
        )

        # Columns with lists
        columns_with_lists = [
            col for col in self.imported_df.columns if self.imported_df[col].dropna().apply(lambda x: isinstance(x, list)).any()
        ]

        for col in columns_with_lists:
            self.imported_df = self.imported_df.explode(col)

        # Check for unexpected fields
        self.validate_data(self.imported_df, pd.DataFrame(columns=columns))

        # Every resource of each task, for the resource pages, and the names joined for display
        self.imported_df["resources"] = self.imported_df["resource"]
        self.imported_df["resource"] = self.imported_df["resources"].map(", ".join)

        # Create child tasks
        for p in definitions:
            name = p["task"]
            self.children[name] = Task(name, self.path)
            self.children[name].imported_df = self.imported_df[self.imported_df["task"] == name]

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        tab = self.html.add_tab("Summary")

        if self.imported_df.empty:
            tab.add_paragraph("Tasks", "No tasks have been defined.")
            super().export_html()
            return

        # Timeline
        tab.add_chart("Task Timeline", create_task_timeline(self.imported_df))

        # Summary Table
        info = self.imported_df.reindex(columns=["task", "project", "workpackage", "description"]).drop_duplicates("task")
        df = info.merge(task_summary_table(self.imported_df), on="task")
        tab.add_table("Tasks", df, units=True,
                      help="All tasks. Start is the date given for the task, or the previous milestone if none was given. "
                           "MISSING means no estimate was provided. Click a task name to open its page. " + TASK_ESTIMATE_HELP)

        add_over_estimate(tab, self.imported_df)

        # Progress
        tab = self.html.add_tab("Progress")
        tab.add_summary("Task Progress Summary", task_summary_stats(self.imported_df),
                        help="Overall progress of every task. Progress is the effort spent as a percentage of effort "
                             "spent plus remaining. Forecast finish is the latest forecast completion of any task.")
        tab.add_chart("Progress by Task", create_task_progress_by_task(self.imported_df),
                      help="One bar per task. The first part is effort spent, the rest is effort remaining (days), so "
                           "the full length is the current estimate for the task. "
                           "Blue is effort within the original estimate (the black line), red is effort past it, so a late task ends in red. Click a bar to open the task page.")

        super().export_html()

def add_over_estimate(tab, df : pd.DataFrame) -> None:
    """
    Add the table of tasks that are over their estimate to a tab, or a line saying there are none

    :param tab: Tab of a page
    :param df: Dataframe of task status updates
    :type df: pd.DataFrame
    :return: None
    """

    over = tasks_over_estimate(df)
    if over.empty:
        tab.add_paragraph("Tasks Over Estimate", "No tasks are over their estimate.", help=TASK_ESTIMATE_HELP)
    else:
        tab.add_table("Tasks Over Estimate", over, units=True, help="Tasks whose spent plus remaining effort is more than their estimate, worst first (by % over). " + TASK_ESTIMATE_HELP)

def create_task_timeline(df: pd.DataFrame, markers=None) -> px.timeline:
    """
    Create a timeline chart from a dataframe

    :param df: Dataframe
    :type df: pd.DataFrame
    :param markers: Markers to add to the chart
    :type markers: dict
    :return: Timeline chart
    :rtype: px.timeline
    """

    # 1. Get start and end date for task
    info = task_info(df)
    df = info.merge(df.reindex(columns=["task", "description"]).groupby("task", as_index=False).first(), on="task")
    df = df.rename(columns={"last_status" : "last_status_date", "remaining" : "remaining_days"})

    # 2. If task isn't complete and today is > last status update the last status date
    df["last_status_date"] = np.where(
                                        df["remaining_days"] != 0,
                                        df["last_status_date"].clip(lower=today),
                                        df["last_status_date"]
    )

    # 3. Calculate end date based on last status and remaining work
    df["end"] = df.apply(
                            lambda row: row["last_status_date"] + pd.offsets.BusinessDay(n=int(np.ceil(row["remaining_days"]))),
                            axis=1
    )

    # 4. Milestone of the task's workpackage, if it has one
    names, dates = [], []
    for r in df.itertuples():
        name, date = None, pd.NaT
        wp = containers.get("workpackage", {}).get(r.workpackage)
        if wp is not None and wp.summary_df is not None and "milestone" in wp.summary_df.columns:
            given = wp.summary_df.loc[wp.summary_df["project"] == r.project, "milestone"].dropna()
            if len(given) and isinstance(given.iloc[0], str):
                ms = project_milestones(r.project)
                due = ms[ms["milestone"] == given.iloc[0]]
                if not due.empty:
                    name, date = given.iloc[0], due["date"].iloc[0]
        names.append(name)
        dates.append(date)
    df["milestone"] = names
    df["milestone date"] = pd.to_datetime(pd.Series(dates, index=df.index))

    # 5. Create the chart
    fig = gantt(
                                            df,
                                            "",
                                            ("start", "Start Date"),
                                            ("end", "End Date"),
                                            ("task", "Task Name"),
                                            markers=markers,
                                            description="description",
                                            link_key="task",
                                            milestones=("milestone", "milestone date"),
                                        )

    return fig

def create_task_progress(df : pd.DataFrame, groupby : str, link_to : tuple=None) -> px.bar:
    """
    Create a stacked bar for allocations

    :param df: Dataframe to create chart from
    :type df: pd.DataFrame
    :param groupby: Column to group by
    :type groupby: str
    :param link_to: Optional (container type, name). Clicking a bar opens that container's page
    :type link_to: tuple
    :return: px.bar
    :rtype: px.bar
    """

    # 1. Calculate boundaries
    start_date = df['status.date'].min() - pd.DateOffset(weeks=2)
    end_date = df['status.date'].max() + pd.DateOffset(weeks=2)

    # 2. Create the full weekly range
    full_range = pd.date_range(start=start_date, end=end_date, freq='W-MON')

    # 3. Pivot and Align
    pivot_df = df.groupby(['status.date', groupby])[['status.spent', 'status.remaining']].sum().unstack(groupby)

    # 4. Reindex to the expanded range and Forward Fill
    # This adds the 2 weeks before and 2 weeks after
    combined_index = pivot_df.index.union(full_range).sort_values()
    expanded_df = pivot_df.reindex(combined_index)
    normalized_df = expanded_df.ffill().reindex(full_range).fillna(0)

    # 5. Collapse and Melt for the chart
    project_totals = normalized_df.T.groupby(level=0).sum().T.reset_index()
    df_melted = project_totals.melt(
                                    id_vars=["index"],
                                    value_vars=["status.spent", "status.remaining"],
                                    var_name="Type",
                                    value_name="Effort"
    )

    # 6. Create a chart per time scale. Spent and remaining are levels, so each period shows its last value
    names = {"status.spent" : "Spent", "status.remaining" : "Remaining"}
    df_melted["Type"] = df_melted["Type"].map(names)
    colors = {n : EFFORT_COLORS[n] for n in names.values()}
    figs = {}
    for scale, (_, x_label, tick_format, hover_format) in SCALES.items():
        figs[scale] = stacked_bar(
                            aggregate_by_period(df_melted, "index", ["Type"], "Effort", scale, "last"),
                            "",
                            ("index", x_label),
                            ("Effort", "Effort (Days)"),
                            "Type",
                            height=1000,
                            bar_width={"Monthly" : 50, "Quarterly" : 80, "Yearly" : 120}[scale],
                            tickformat=tick_format,
                            hover_date_format=hover_format,
                            colors=colors,
                            descriptions={k : f"Click to open {link_to[0]} {link_to[1]}" for k in colors} if link_to else None,
                            link_to=link_to,
                        )

    return figs

def parse_task(definition : dict, known : set) -> dict:
    """
    Check a task definition and convert it to the form used by the report

    Effort (the estimate, and spent and remaining in each status update) is converted to man-days. It is a number
    and a unit, e.g. "3 mw", in md, mw, mm or my, or a plain number in the task_unit of the format (md by default).
    The resource is a name or a list of names, which become a tuple.

    :param definition: Task definition as given in the input
    :type definition: dict
    :param known: Names of the resources that are defined
    :type known: set
    :return: Copy of the definition with effort in days and the resources as a tuple
    :rtype: dict
    """

    d = dict(definition)
    name = d["task"]
    unit = _format.active().task_unit

    # Rounded so that the same effort in different units is equal, e.g. "0.1 my" and "24 md"
    def days(value, where, allow_zero):
        months = parse_effort(value, where, default_unit=unit, allow_zero=allow_zero)
        return None if months is None else round(months * DAYS_PER_MONTH, 6)

    # Resources: one name or a list of them, each defined in the resources
    given = d.get("resource")
    names = given if isinstance(given, list) else [given]
    if given is None or not names:
        raise ValueError(f"task {name} has no resource. Give a resource, or a list of resources for a task shared by several people")
    for r in names:
        if not isinstance(r, str) or r.strip() == "":
            raise ValueError(f"task {name} resource {r!r} must be the name of a resource")
    repeated = sorted({r for r in names if names.count(r) > 1})
    if repeated:
        raise ValueError(f"task {name} lists resource {', '.join(repeated)} more than once")
    unknown = [r for r in names if r not in known]
    if unknown:
        raise ValueError(f"task {name} resource {', '.join(unknown)} is not defined in the resources")
    d["resource"] = tuple(names)

    # Original estimate
    if "estimate" in d:
        d["estimate"] = days(d["estimate"], f"task {name} estimate {d['estimate']!r}", allow_zero=False)

    # Status updates
    status = d.get("status")
    if not isinstance(status, list) or not status:
        raise ValueError(f"task {name} has no status updates")
    updates = []
    for i, u in enumerate(status, 1):
        if not isinstance(u, dict):
            raise ValueError(f"task {name} status update {i} must have a date, spent and remaining, got {u!r}")
        u = dict(u)
        for field in ("date", "spent", "remaining"):
            if u.get(field) is None:
                raise ValueError(f"task {name} status update {i} has no {field}")
        date = pd.to_datetime(smart_date_converter(u["date"]), errors="coerce")
        if pd.isna(date):
            raise ValueError(f"task {name} status update {i} has an invalid date {u['date']!r}")
        u["date"] = date
        for field in ("spent", "remaining"):
            u[field] = days(u[field], f"task {name} status update {i} ({date:%Y-%m-%d}) {field} {u[field]!r}", allow_zero=True)
        updates.append(u)
    dates = [u["date"] for u in updates]
    if len(set(dates)) != len(dates):
        repeated = sorted({f"{x:%Y-%m-%d}" for x in dates if dates.count(x) > 1})
        raise ValueError(f"task {name} has more than one status update on {', '.join(repeated)}")
    d["status"] = updates

    return d

def latest_task_status(df : pd.DataFrame) -> pd.DataFrame:
    """
    Latest status of each task, with the percentage of the work that is complete

    :param df: Dataframe of task status updates
    :type df: pd.DataFrame
    :return: One row per task
    :rtype: pd.DataFrame
    """

    latest = df.sort_values("status.date").groupby("task", as_index=False).last()
    total = latest["status.spent"] + latest["status.remaining"]
    latest["complete"] = np.where(total > 0, 100 * latest["status.spent"] / total.where(total > 0, 1), 100.0)
    return latest

MISSING = '<span class="badge badge-missing">MISSING</span>'
""" Shown in place of a value that has not been provided """

def project_milestones(project : str) -> pd.DataFrame:
    """
    Milestones of a project, in date order

    :param project: Name of the project
    :type project: str
    :return: Dataframe with milestone, date (when it is due, i.e. the end of a window) and start (windows
             only) columns. Empty if there are none
    :rtype: pd.DataFrame
    """

    empty = pd.DataFrame({"milestone" : [], "date" : pd.to_datetime([]), "start" : pd.to_datetime([])})

    proj = containers.get("project", {}).get(project)
    if proj is None or proj.imported_df is None or "milestones" not in proj.imported_df.columns:
        return empty

    items = [m for m in proj.imported_df["milestones"].tolist() if isinstance(m, dict)]
    if not items:
        return empty

    ms = pd.DataFrame(items)
    for col in ("date", "start", "end"):
        ms[col] = pd.to_datetime(ms[col], errors="coerce") if col in ms.columns else pd.NaT
    ms["date"] = ms["end"].fillna(ms["date"])
    ms = ms[["milestone", "date", "start"]]
    return ms.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

def task_info(df : pd.DataFrame) -> pd.DataFrame:
    """
    One row per task with its resolved start date, estimate and latest progress.

    The start date is the one given for the task. If there isn't one it defaults to the date of the
    previous milestone: the latest milestone of the project dated on or before the task's first
    status update. If the project has no such milestone the project start date, and finally the first
    status update, is used. The estimate is never defaulted: tasks without one are flagged.

    :param df: Dataframe of task status updates
    :type df: pd.DataFrame
    :return: One row per task. Dates are timestamps and missing estimates are NaN
    :rtype: pd.DataFrame
    """

    d = df.sort_values("status.date").copy()
    for col in ("start", "estimate", "resource", "project", "workpackage"):
        if col not in d.columns:
            d[col] = np.nan

    g = d.groupby("task", as_index=False).agg(
                                                project=("project", "last"),
                                                workpackage=("workpackage", "last"),
                                                resource=("resource", "last"),
                                                given_start=("start", "first"),
                                                estimate=("estimate", "first"),
                                                first_status=("status.date", "first"),
                                                last_status=("status.date", "last"),
                                                spent=("status.spent", "last"),
                                                remaining=("status.remaining", "last"),
                                            )

    g["given_start"] = pd.to_datetime(g["given_start"], errors="coerce")
    g["first_status"] = pd.to_datetime(g["first_status"])
    g["last_status"] = pd.to_datetime(g["last_status"])
    g["estimate"] = pd.to_numeric(g["estimate"], errors="coerce")

    # Start dates
    starts, notes = [], []
    for r in g.itertuples():
        if pd.notna(r.given_start):
            starts.append(r.given_start)
            notes.append("")
            continue

        ms = project_milestones(r.project)
        previous = ms[ms["date"] <= r.first_status]
        if not previous.empty:
            starts.append(previous["date"].iloc[-1])
            notes.append(f"default: {previous['milestone'].iloc[-1]}")
            continue

        proj = containers.get("project", {}).get(r.project)
        proj_start = pd.NaT
        if proj is not None and proj.imported_df is not None and "start" in proj.imported_df.columns:
            proj_start = pd.to_datetime(proj.imported_df["start"].iloc[0], errors="coerce")
        if pd.notna(proj_start):
            starts.append(proj_start)
            notes.append("default: project start")
        else:
            starts.append(r.first_status)
            notes.append("default: first status")

    g["start"] = starts
    g["start_note"] = notes

    # Forecast completion: latest status (not before today, or the start date, if unfinished) plus remaining working days
    base = pd.Series(np.where(g["remaining"] != 0, g["last_status"].clip(lower=today), g["last_status"]), index=g.index)
    base = pd.Series(np.where(g["remaining"] != 0, np.maximum(base, g["start"]), base), index=g.index)
    g["forecast_end"] = [b + pd.offsets.BusinessDay(n=int(np.ceil(r))) for b, r in zip(base, g["remaining"], strict=True)]

    total = g["spent"] + g["remaining"]
    g["total"] = total
    g["complete"] = np.where(total > 0, 100 * g["spent"] / total.where(total > 0, 1), 100.0)
    g["status"] = np.where(g["remaining"] == 0, "Complete", np.where(g["spent"] == 0, "Not started", "In progress"))
    g["has_estimate"] = g["estimate"].notna()
    g["over_by"] = np.where(g["has_estimate"], g["total"] - g["estimate"], 0.0)
    g["over"] = g["has_estimate"] & (g["over_by"] > 0)

    return g

def over_badge(days : float) -> str:
    """ Html badge marking a task that is past its estimate, by the given number of days """
    return f'<span class="badge badge-over">+{format_days(days)}</span>'

OVER_ESTIMATE = '<span class="badge badge-over">OVER ESTIMATE</span>'
""" Shown against a task whose spent plus remaining effort is more than its estimate """

WITHIN_ESTIMATE = '<span class="badge badge-upcoming">Within estimate</span>'
""" Shown against a task whose spent plus remaining effort is no more than its estimate """

TASK_ESTIMATE_HELP = ("Estimate is the original estimate of the effort for the task. A task is OVER ESTIMATE when the effort spent "
                 "plus the effort remaining is more than its estimate, even if the extra effort has not been spent yet. "
                 "Already spent past the estimate means the over-run has happened, not just been forecast. "
                 "Tasks with no estimate cannot be checked. Effort is shown in the unit chosen in the Units box.")
""" Hover guidance for the task estimate columns """

def estimate_check(r) -> str:
    """
    Html saying whether a task is within its estimate, and if not by how much it is over

    :param r: Row of task_info
    :return: Html
    :rtype: str
    """

    if not r.has_estimate:
        return "No estimate"
    if not r.over:
        return f"{WITHIN_ESTIMATE} {format_days(r.total)} of {format_days(r.estimate)} ({r.total / r.estimate:.0%})"
    over = f"{format_days(r.over_by)} over the estimate of {format_days(r.estimate)} (+{r.over_by / r.estimate:.0%})"
    if r.spent <= r.estimate:
        return f"{OVER_ESTIMATE} spent + remaining {format_days(r.total)} is {over}"
    if r.remaining == 0:
        return f"{OVER_ESTIMATE} finished in {format_days(r.spent)}, {over}"
    return (f"{OVER_ESTIMATE} already spent {format_days(r.spent)}, past the estimate. With {format_days(r.remaining)} "
            f"still to do it is {over}")

def tasks_over_estimate(df : pd.DataFrame) -> pd.DataFrame:
    """
    Tasks that are past their estimate, i.e. spent plus remaining effort is more than the estimate

    :param df: Dataframe of task status updates
    :type df: pd.DataFrame
    :return: One row per task that is over its estimate, worst first (by the fraction over). Effort is html
    :rtype: pd.DataFrame
    """

    g = task_info(df)
    g = g[g["over"]]
    g = g.assign(_pct=g["over_by"] / g["estimate"]).sort_values(["_pct", "over_by"], ascending=False)

    return pd.DataFrame({
        "task" : g["task"],
        "workpackage" : g["workpackage"],
        "resource" : g["resource"],
        "status" : g["status"],
        "estimate" : [format_days(v) for v in g["estimate"]],
        "spent" : [format_days(v) for v in g["spent"]],
        "remaining" : [format_days(v) for v in g["remaining"]],
        "over by" : [over_badge(v) for v in g["over_by"]],
        "% over" : (100 * g["_pct"]).round(0).astype(int),
        "problem" : [estimate_check(r) for r in g.itertuples()],
    }).reset_index(drop=True)

def task_summary_table(df : pd.DataFrame) -> pd.DataFrame:
    """
    Summarise the progress of each task

    :param df: Dataframe of task status updates
    :type df: pd.DataFrame
    :return: One row per task. Missing estimates are flagged in the estimate column. Effort is html, see format_days
    :rtype: pd.DataFrame
    """

    g = task_info(df)

    def show_start(r):
        text = r.start.strftime("%Y-%m-%d")
        return f"{text} ({r.start_note})" if r.start_note else text

    def show_variance(r):
        if not r.has_estimate:
            return "&ndash;"
        if r.over:
            return over_badge(r.over_by)
        return format_days(r.over_by)

    out = pd.DataFrame({
        "task" : g["task"],
        "resource" : g["resource"],
        "status" : g["status"],
        "start" : [show_start(r) for r in g.itertuples()],
        "last_status" : g["last_status"],
        "forecast_end" : g["forecast_end"],
        "estimate" : [format_days(e) if pd.notna(e) else MISSING for e in g["estimate"]],
        "spent" : [format_days(v) for v in g["spent"]],
        "remaining" : [format_days(v) for v in g["remaining"]],
        "variance" : [show_variance(r) for r in g.itertuples()],
        "% complete" : g["complete"].round(0).astype(int),
        "estimate check" : [estimate_check(r) for r in g.itertuples()],
    })

    return out

def milestone_task_summary(tasks : pd.DataFrame, milestones : pd.DataFrame=None, tasks_href : str=None) -> pd.DataFrame:
    """
    Summarise the status of tasks by milestone.

    Tasks have no milestone of their own, so each task is attributed to the first milestone
    dated on or after the task's forecast completion, i.e. the milestone it is needed by.
    Tasks forecast to finish after the last milestone are listed under "After <last milestone>".
    The current milestone is the next one due (first dated today or later).

    :param tasks: Dataframe of task status updates
    :type tasks: pd.DataFrame
    :param milestones: Dataframe with milestone, date and description columns, or None if the project has none
    :type milestones: pd.DataFrame
    :param tasks_href: If given, the task counts link to this page
    :type tasks_href: str
    :return: One row per milestone. The "when" and "% complete" columns contain html
    :rtype: pd.DataFrame
    """

    t = task_info(tasks)

    # Milestones, in date order
    if milestones is None or milestones.empty:
        ms = pd.DataFrame({"milestone" : ["(no milestones)"], "date" : [pd.NaT], "description" : ["Project has no milestones"], "start" : [pd.NaT]})
        t["_ms"] = 0
    else:
        ms = milestones.reindex(columns=["milestone", "date", "description", "start"])
        ms["date"] = pd.to_datetime(ms["date"], errors="coerce")
        ms["start"] = pd.to_datetime(ms["start"], errors="coerce")
        ms = ms.sort_values("date").reset_index(drop=True)

        def assign(end):
            for i, d in enumerate(ms["date"]):
                if pd.notna(d) and end <= d:
                    return i
            return len(ms)

        t["_ms"] = t["forecast_end"].apply(assign)

        # Tasks finishing after the last milestone
        if (t["_ms"] == len(ms)).any():
            ms.loc[len(ms)] = [f"After {ms['milestone'].iloc[-1]}", pd.NaT, "Tasks forecast to finish after the last milestone", pd.NaT]

    # Current milestone: the next one due
    ms["when"] = milestone_badges(ms["date"])
    ms["text"] = milestone_dates_text(ms["start"], ms["date"])

    rows = []
    for i, m in ms.iterrows():
        sel = t[t["_ms"] == i]
        spent, remaining = float(sel["spent"].sum()), float(sel["remaining"].sum())
        total = spent + remaining
        pct = 100 * spent / total if total > 0 else (100 if len(sel) else None)

        when = m["when"]

        bar = "&ndash;" if pct is None else f'<div class="pbar" style="--pct:{pct:.0f}%"><span>{pct:.0f}%</span></div>'

        rows.append({
            "milestone" : m["milestone"],
            "date" : m["text"],
            "description" : m["description"],
            "when" : when,
            "tasks" : (f'<a href="{_html.escape(tasks_href, quote=True)}" '
                       f'data-tip="Open the tasks page, filtered to this project\'s tasks.">{len(sel)}</a>')
                      if tasks_href and len(sel) else len(sel),
            "complete" : int((sel["status"] == "Complete").sum()),
            "in progress" : int((sel["status"] == "In progress").sum()),
            "not started" : int((sel["status"] == "Not started").sum()),
            "no estimate" : int((~sel["has_estimate"]).sum()),
            "over estimate" : (f'<span class="badge badge-over">{int(sel["over"].sum())} task(s), '
                               f'+{format_days(sel.loc[sel["over"], "over_by"].sum())}</span>'
                               if sel["over"].any() else 0),
            "spent" : format_days(spent),
            "remaining" : format_days(remaining),
            "% complete" : bar,
        })

    return pd.DataFrame(rows)

def task_summary_stats(df : pd.DataFrame) -> list:
    """
    Overall progress of a set of tasks

    :param df: Dataframe of task status updates
    :type df: pd.DataFrame
    :return: List of (label, value) pairs
    :rtype: list
    """

    t = task_info(df)
    spent = float(t["spent"].sum())
    remaining = float(t["remaining"].sum())
    total = spent + remaining
    pct = 100 * spent / total if total > 0 else 100

    def days(v):
        return f"{v:,.1f}".rstrip("0").rstrip(".")

    return [
        ("Overall progress", f"{pct:.0f}%"),
        ("Tasks", str(len(t))),
        ("Complete", str((t["status"] == "Complete").sum())),
        ("In progress", str((t["status"] == "In progress").sum())),
        ("Not started", str((t["status"] == "Not started").sum())),
        ("Days spent", days(spent)),
        ("Days remaining", days(remaining)),
        ("Forecast finish", t["forecast_end"].max().strftime("%Y-%m-%d")),
        ("Missing estimates", str(int((~t["has_estimate"]).sum())), int((~t["has_estimate"]).sum()) > 0),
        ("Over estimate", str(int(t["over"].sum())), bool(t["over"].any())),
    ]

def create_task_progress_by_task(df : pd.DataFrame, bar_height=50) -> go.Figure:
    """
    Create a bar for each task showing the effort spent and the effort remaining.

    Each bar is split at the task's original estimate: effort within the estimate is drawn in blue and
    effort past it in red, so a task that is on track is all blue and a late one ends in red. Tasks with
    no estimate cannot be checked and are drawn in blue.

    :param df: Dataframe of task status updates
    :type df: pd.DataFrame
    :param bar_height: Height of each bar
    :type bar_height: int
    :return: Chart
    :rtype: go.Figure
    """

    latest = task_info(df)
    spent = latest["spent"].astype(float)
    remaining = latest["remaining"].astype(float)
    total = spent + remaining
    estimate_text = [f"{e:g} days" if pd.notna(e) else "MISSING" for e in latest["estimate"]]
    over_text = [f"<br>Past estimate by {o:g} days" if o > 0 else "" for o in latest["over_by"].where(latest["over"], 0)]
    custom = np.column_stack([latest["complete"], estimate_text, over_text])

    # Split each bar at the estimate. Without an estimate everything counts as within it
    estimate = latest["estimate"].astype(float).fillna(np.inf)
    within_end = np.minimum(total, estimate)
    segments = (
        ("Spent",                   0 * spent,                   np.minimum(spent, estimate)),
        ("Spent past estimate",     estimate.clip(upper=spent),  (spent - estimate).clip(lower=0)),
        ("Remaining",               spent,                       (within_end - spent).clip(lower=0)),
        ("Remaining past estimate", np.maximum(spent, estimate), (total - np.maximum(spent, estimate)).clip(lower=0)),
    )

    fig = go.Figure()
    for name, base, value in segments:
        # Spent and remaining are always in the key; the past estimate parts only when a task is late
        if "past" in name and not (value > 0).any():
            continue
        show = value > 0
        fig.add_trace(go.Bar(
            orientation="h",
            name=name,
            y=latest["task"][show],
            x=value[show],
            base=base[show],
            customdata=custom[show.to_numpy()],
            marker=dict(color=EFFORT_COLORS[name]),
            legendgroup=name,
            hovertemplate=("<b>%{y}</b><br>" + name + ": %{x:.4~g} days<br>"
                           "%{customdata[0]:.0f}% complete<br>Estimate: %{customdata[1]}%{customdata[2]}<extra></extra>"),
        ))

    style_axes(fig)
    fig.update_layout(barmode="overlay", meta={"link_key": "task"})
    _shade_bars(fig, BAR_WIDTH)

    # Estimate marker across each bar that has one
    has = latest["has_estimate"]
    fig.add_trace(go.Scatter(
        x=latest.loc[has, "estimate"],
        y=latest.loc[has, "task"],
        mode="markers",
        name="Estimate",
        marker=dict(symbol="line-ns", size=26, line=dict(width=3, color="#1c2433"), color="#1c2433"),
        hovertemplate="<b>%{y}</b><br>Estimate: %{x:.4~g} days<extra></extra>",
    ))

    # Percentage complete at the end of each bar. Tasks with no estimate are flagged in red
    end = spent + remaining
    for flagged in (False, True):
        sel = (~has) if flagged else has
        fig.add_trace(go.Scatter(
            x=end[sel],
            y=latest.loc[sel, "task"],
            mode="text",
            text=[f"{c:.0f}% complete" + ("  \u26a0 NO ESTIMATE" if flagged else "") for c in latest.loc[sel, "complete"]],
            textposition="middle right",
            textfont=dict(size=12, color="#d62839") if flagged else dict(size=12),
            hoverinfo="skip",
            showlegend=False,
            cliponaxis=False,
        ))

    # Leave room after the longest bar (or estimate) for its label, so it is not drawn under the legend
    longest = max(float(end.max()), float(latest["estimate"].max()) if has.any() else 0.0, 1.0)
    room = 0.4 if (~has).any() else 0.2
    fig.update_xaxes(title="Effort (Days)", range=[0, longest * (1 + room)])
    fig.update_yaxes(title="Task Name", autorange="reversed")
    fig.update_layout(
        height=len(latest) * bar_height + 120,
        autosize=True,
        margin=dict(l=50, r=200, t=50, b=50),
        legend=dict(x=1.01, xanchor="left", y=1, yanchor="top", bordercolor="#b7c2d6", borderwidth=1),
    )

    return fig

__all__ = [
    "tasks_over_estimate",
    "add_over_estimate",
    "parse_task",
    "estimate_check",
    "TASK_ESTIMATE_HELP",
    "milestone_task_summary",
    "task_summary_table",
    "task_summary_stats",
    "latest_task_status",
    "create_task_progress_by_task",
    "Task",
    "Tasks",
    "create_task_timeline",
    "create_task_progress",
]
