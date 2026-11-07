from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from ._charts import SCALES, color_map, gantt, stacked_bar
from ._containers import Container, containers
from ._tasks import create_task_progress_by_task, create_task_timeline, task_summary_stats, task_summary_table
from ._utils import default_end_date, today
from ._workpackages import create_allocation_chart


def create_availability_chart(df : pd.DataFrame, scale : str, colors : dict=None) -> go.Figure:
    """
    Create a stacked bar showing how many resources are available over time.

    Each bar covers one period (month / quarter / year) and has one segment per resource
    that is available at any point in that period, so the bar height is the number of
    resources that can be called on in the period. Resources with no end date are
    treated as available to the same horizon as the Gantt charts.

    :param df: Resource dataframe with resource, start and end columns
    :type df: pd.DataFrame
    :param scale: One of SCALES
    :type scale: str
    :param colors: Optional dictionary of resource to colour, so colours match other charts
    :type colors: dict
    :return: Figure
    :rtype: go.Figure
    """

    freq, x_label, tick_format, hover_format = SCALES[scale]

    d = df[["resource", "start", "end"]].copy()
    d["start"] = pd.to_datetime(d["start"], errors="coerce")
    d["end"] = pd.to_datetime(d["end"], errors="coerce")

    horizon = max(d["end"].max(), default_end_date)
    d["end"] = d["end"].fillna(horizon)
    d["start"] = d["start"].fillna(d["start"].min())

    # Periods covering the whole range
    first = d["start"].min().to_period(freq[0]).start_time
    periods = pd.date_range(first, horizon, freq=freq)

    rows = []
    for p in periods:
        p_end = p + pd.tseries.frequencies.to_offset(freq) - pd.Timedelta(days=1)
        for r in d.itertuples():
            if r.start <= p_end and r.end >= p:
                rows.append({"period": p, "resource": r.resource, "available": 1})

    plot_df = pd.DataFrame(rows, columns=["period", "resource", "available"])
    bar_width = {"Monthly" : 28, "Quarterly" : 50, "Yearly" : 90}[scale]

    fig = stacked_bar(
        plot_df,
        "",
        ("period", x_label),
        ("available", "Resources available"),
        "resource",
        height=520,
        bar_width=bar_width,
        link_key="resource",
        tickformat=tick_format,
        hover_date_format=hover_format,
        colors=colors,
        legend_outside=True,
    )

    # Total above each bar, and whole number axis
    totals = plot_df.groupby("period")["available"].sum()
    fig.add_trace(go.Scatter(
        x=totals.index,
        y=totals.values,
        mode="text",
        text=[str(int(v)) for v in totals.values],
        textposition="top center",
        textfont=dict(size=12, color="#1c2433"),
        hoverinfo="skip",
        showlegend=False,
        cliponaxis=False,
    ))
    fig.update_yaxes(dtick=1, rangemode="tozero")

    return fig

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

        # Use the colour this resource has on the overview page
        index = containers.get("resources", {}).get("index")
        colors = color_map(index.imported_df["resource"]) if index is not None and index.imported_df is not None else None

        # Add availability gantt
        tab = self.html.add_tab("Availability")
        tab.add_chart("Availability", gantt(
                                                df,
                                                "",
                                                ("start", "Start Date"),
                                                ("end", "End Date"),
                                                ("resource", "Resource Name"),
                                                markers={"Today" : today},
                                                link_key="resource",
                                                colors=colors,
                                            )
        )

        self.add_allocations()
        self.add_tasks()

        # Add details table
        tab = self.html.add_tab("Details")
        tab.add_table("Resource Details", df, transpose=True, help="Definition of this resource as given in the resources input file.")

        super().export_html()

    def add_allocations(self) -> None:
        """
        Add a tab showing how this resource is allocated to projects and workpackages

        :return: None
        """

        index = containers.get("workpackages", {}).get("index")
        if index is None or index.imported_df is None or "allocations.resource" not in index.imported_df.columns:
            return

        a = index.imported_df
        a = a[a["allocations.resource"] == self.name].copy()
        if a.empty:
            return

        # Effort of each allocation = fraction of a person x number of months
        start = pd.to_datetime(a["allocations.start"])
        end = pd.to_datetime(a["allocations.end"])
        a["months"] = (end.dt.year - start.dt.year) * 12 + (end.dt.month - start.dt.month) + 1
        a["effort"] = a["allocations.allocation"] * a["months"]
        a["start"] = start
        a["end"] = end

        by_workpackage = a.rename(columns={"allocations.allocation": "allocation"})[
            ["project", "workpackage", "start", "end", "allocation", "months", "effort"]]
        by_workpackage = by_workpackage.sort_values(["project", "workpackage", "start"]).reset_index(drop=True)

        by_project = a.groupby("project", as_index=False).agg(
            workpackages=("workpackage", lambda x: ", ".join(sorted(set(x)))),
            start=("start", "min"),
            end=("end", "max"),
            effort=("effort", "sum"),
        )

        tab = self.html.add_tab("Allocations")
        tab.add_chart("Allocation by Project", create_allocation_chart(a, "project"),
                      help="Effort allocated to this resource each period, stacked by project. "
                           "Click a segment to open the project page.")
        tab.add_chart("Allocation by Workpackage", create_allocation_chart(a, "workpackage"),
                      help="Effort allocated to this resource each period, stacked by workpackage. "
                           "Click a segment to open the workpackage page.")
        tab.add_table("Projects", by_project,
                      help="Total effort this resource is allocated to each project, in person-months.")
        tab.add_table("Workpackages", by_workpackage,
                      help="Each allocation of this resource to a workpackage. Allocation is the fraction of a "
                           "person per month (1.0 = full time); effort is allocation x months, in person-months.")

    def add_tasks(self) -> None:
        """
        Add a tab showing the progress of every task this resource is associated with

        :return: None
        """

        index = containers.get("tasks", {}).get("index")
        if index is None or index.imported_df is None or "resource" not in index.imported_df.columns:
            return

        t = index.imported_df
        t = t[t["resource"] == self.name]
        if t.empty:
            return

        tab = self.html.add_tab("Tasks")
        tab.add_summary("Task Progress Summary", task_summary_stats(t),
                        help="Overall progress of every task this resource is associated with. Overall progress is the "
                             "effort spent as a percentage of effort spent plus remaining. Forecast finish is the latest "
                             "forecast completion of any of their tasks.")
        tab.add_chart("Progress by Task", create_task_progress_by_task(t),
                      help="One bar per task this resource works on. The first part is effort spent, the rest is effort "
                           "remaining (days), so the full length is the current estimate for the task. "
                           "Blue is effort within the original estimate (the black line), red is effort past it, so a late task ends in red. "
                           "Click a bar to open the task page.")
        tab.add_chart("Task Timeline", create_task_timeline(t, markers={"Today" : today}))
        tab.add_table("Tasks", task_summary_table(t),
                      help="Progress of every task this resource is associated with. Spent and remaining are in days; "
                           "remaining of 0 means the task is complete.")

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

    def import_data(self, definitions : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param definitions: List of dictionaries
        :return: None
        """

        self.check_definitions(definitions, "resource")
        super().import_data(definitions)
        if self.imported_df.empty:
            self.imported_df = pd.DataFrame(columns=["resource", "uname", "start", "end", "profile"])
        self.validate_data(self.imported_df, pd.DataFrame(columns=["resource", "uname", "start", "end", "profile"]))

        # Create child resources
        for p in definitions:
            name = p["resource"]
            self.children[name] = Resource(name, self.path)
            self.children[name].import_data([p])

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Summary Table
        df = pd.DataFrame(columns=["resource", "uname", "start", "end", "profile"])
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)

        if df.empty:
            tab = self.html.add_tab("Resources")
            tab.add_paragraph("Resources", "No resources have been defined.")
            super().export_html()
            return

        # One colour per resource, shared by every chart on this page
        colors = color_map(df["resource"])

        # Add Gantt to html
        tab = self.html.add_tab("Availability")
        tab.add_chart("Resource Availability", gantt(
                                                        df,
                                                        "",
                                                        ("start", "Start Date"),
                                                        ("end", "End Date"),
                                                        ("resource", "Resource Name"),
                                                        markers={"Today" : today},
                                                        link_key="resource",
                                                        colors=colors,
                                                        show_legend=True,
                                                    )
        )

        # Add stacked availability chart, with a choice of scale
        tab.add_scaled_chart("Resources Available Over Time",
                             {scale : create_availability_chart(df, scale, colors) for scale in SCALES},
                             label="Scale",
                             help="Number of resources available in each period. Each coloured segment is one resource "
                                  "and counts if it is available at any point in the period, so the bar height (also "
                                  "printed above the bar) is the number of resources that could be called on. "
                                  "Resources with no end date are assumed available to the end of the Gantt chart above. "
                                  "Click a segment to open that resource's page.")

        # Add table to html
        tab = self.html.add_tab("Resources")
        tab.add_table("Resources", df)

        super().export_html()

__all__ = [
    "Resources",
]
