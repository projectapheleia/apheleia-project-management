from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ._charts import INK, SCALES, color_map, gantt, stacked_bar, style_axes
from ._containers import Container, containers
from ._tasks import (
    TASK_ESTIMATE_HELP,
    add_over_estimate,
    create_task_progress_by_task,
    create_task_timeline,
    task_summary_stats,
    task_summary_table,
)
from ._utils import default_end_date, smart_date_converter, today
from ._workpackages import create_allocation_chart

COLUMNS = ["resource", "uname", "start", "end", "availability", "profile"]
""" Columns of the imported dataframe: one row per availability period of each resource """

FIELDS = ["resource", "uname", "start", "end", "availability", "profile", "periods"]
""" Fields permitted in a resource definition """

PERIOD_FIELDS = ["start", "end", "availability"]
""" Fields permitted in each entry of a resource's periods """

NO_ACTIVE_PERIOD = "0% (no active period)"
""" Shown as the availability today of a resource with no period covering today """

def _parse_date(value, resource : str, where : str, field : str) -> pd.Timestamp:
    """
    Convert a date given in a resource definition to a timestamp

    :param value: Date as given in the input file
    :param resource: Name of the resource, for error messages
    :type resource: str
    :param where: Period the date was given in, for error messages, e.g. "period 2"
    :type where: str
    :param field: Which date it is, "start" or "end", for error messages
    :type field: str
    :return: Timestamp, or NaT if no date was given
    :rtype: pd.Timestamp
    """

    value = smart_date_converter(value) if isinstance(value, str) else value
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return pd.NaT
    try:
        return pd.Timestamp(value)
    except (ValueError, TypeError):
        raise ValueError(f"resource {resource} has an invalid {field} date in {where}: {value!r}. Dates are written as YYYY-MM-DD") from None

def _parse_availability(value, resource : str, where : str) -> float:
    """
    Convert an availability given in a resource definition to a percentage

    :param value: Availability as given in the input file. None or empty is 100
    :param resource: Name of the resource, for error messages
    :type resource: str
    :param where: Period the availability was given in, for error messages
    :type where: str
    :return: Percentage between 0 and 100
    :rtype: float
    """

    if value is None or (isinstance(value, str) and value.strip().lower() in ["", "none", "null", "nan"]):
        return 100.0
    if isinstance(value, float) and pd.isna(value):
        return 100.0

    number = None
    if not isinstance(value, bool):
        try:
            number = float(value.strip().rstrip("%")) if isinstance(value, str) else float(value)
        except (ValueError, TypeError):
            number = None

    if number is None or pd.isna(number) or number < 0 or number > 100:
        raise ValueError(f"resource {resource} has an invalid availability in {where}: {value!r}. "
                         "Availability is a percentage between 0 and 100")
    return number

def resource_periods(definition : dict) -> list[dict]:
    """
    The availability periods of a resource definition, checked and sorted by start date

    A resource gives its periods either as a list in periods, or as a single period with start, end
    and availability at the top level. Each period has an optional availability, a percentage
    between 0 and 100 that defaults to 100. Only the first period can have no start and only the last
    can have no end. Periods must not overlap; time between periods is time the resource is not available.

    :param definition: Resource definition
    :type definition: dict
    :return: List of dictionaries with start, end and availability
    :rtype: list[dict]
    """

    name = definition["resource"]
    top_level = [k for k in PERIOD_FIELDS if k in definition]

    if "periods" in definition:
        if top_level:
            raise ValueError(f"resource {name} has both periods and {', '.join(top_level)}. "
                             "Give its dates either as a list of periods or as a single start and end, not both")
        raw = definition["periods"]
        if not isinstance(raw, list) or len(raw) == 0:
            raise ValueError(f"resource {name} has no periods. Give at least one period, each with a start and an end date, or remove periods")
        for i, r in enumerate(raw, start=1):
            if not isinstance(r, dict):
                raise ValueError(f"resource {name} period {i} must have start, end and availability fields, but is: {r!r}")
            unexpected = sorted(set(r) - set(PERIOD_FIELDS))
            if unexpected:
                raise ValueError(f"resource {name} period {i} contains unexpected fields: {', '.join(unexpected)}. "
                                 f"Expected fields are: {', '.join(PERIOD_FIELDS)}")
        labelled = [(f"period {i}", r) for i, r in enumerate(raw, start=1)]
    else:
        labelled = [("its definition", {k : definition[k] for k in top_level})]

    periods = []
    for where, r in labelled:
        p = {
            "start" : _parse_date(r.get("start"), name, where, "start"),
            "end" : _parse_date(r.get("end"), name, where, "end"),
            "availability" : _parse_availability(r.get("availability"), name, where),
            "where" : where,
        }
        if pd.notna(p["start"]) and pd.notna(p["end"]) and p["end"] < p["start"]:
            raise ValueError(f"resource {name} has an end date ({p['end']:%Y-%m-%d}) before its start date ({p['start']:%Y-%m-%d}) in {where}")
        periods.append(p)

    # Sort by start, with a missing start first
    periods.sort(key=lambda p: pd.Timestamp.min if pd.isna(p["start"]) else p["start"])

    for i, p in enumerate(periods):
        if i > 0 and pd.isna(p["start"]):
            raise ValueError(f"resource {name} {p['where']} has no start. Only the first period can have no start")
        if i < len(periods) - 1 and pd.isna(p["end"]):
            raise ValueError(f"resource {name} {p['where']} has no end. Only the last period can have no end")
        if i > 0 and p["start"] <= periods[i - 1]["end"]:
            prev = periods[i - 1]
            raise ValueError(f"resource {name} {prev['where']} ({prev['start']:%Y-%m-%d} to {prev['end']:%Y-%m-%d}) "
                             f"overlaps {p['where']} (starting {p['start']:%Y-%m-%d}). Periods must not overlap")

    return [{k : p[k] for k in PERIOD_FIELDS} for p in periods]

def availability_text(value) -> str:
    """
    Availability as text for tables and hover, e.g. 50%

    :param value: Percentage
    :return: str
    """

    return "" if pd.isna(value) else f"{value:g}%"

def availability_on(df : pd.DataFrame, date : pd.Timestamp) -> pd.Series:
    """
    Availability of each resource on a date

    :param df: Resource dataframe, one row per period
    :type df: pd.DataFrame
    :param date: Date
    :type date: pd.Timestamp
    :return: Percentage available on the date, by resource. NaN if no period covers the date
    :rtype: pd.Series
    """

    start = pd.to_datetime(df["start"]).fillna(pd.Timestamp.min)
    end = pd.to_datetime(df["end"]).fillna(pd.Timestamp.max)
    covers = (start <= date) & (end >= date)
    value = df["availability"].where(covers).astype(float)
    return value.groupby(df["resource"], sort=False).max()

def available_today_text(value) -> str:
    """
    Availability today as text for tables, saying when no period covers today

    :param value: Percentage, or NaN if no period covers today
    :return: str
    """

    return NO_ACTIVE_PERIOD if pd.isna(value) else availability_text(value)

def resource_summary(df : pd.DataFrame) -> pd.DataFrame:
    """
    One row per resource: first start, last end and availability today

    :param df: Resource dataframe, one row per period
    :type df: pd.DataFrame
    :return: Dataframe with resource, uname, start, end, available today and profile
    :rtype: pd.DataFrame
    """

    d = df.copy()
    d["start"] = pd.to_datetime(d["start"])
    d["end"] = pd.to_datetime(d["end"])
    summary = d.groupby("resource", as_index=False, sort=False).agg(
        uname=("uname", "first"),
        start=("start", lambda x: x.min() if x.notna().all() else pd.NaT),
        end=("end", lambda x: x.max() if x.notna().all() else pd.NaT),
        periods=("resource", "size"),
        profile=("profile", "first"),
    )
    now = availability_on(d, today)
    summary.insert(4, "available today", [available_today_text(now.get(r)) for r in summary["resource"]])
    return summary

def period_table(df : pd.DataFrame) -> pd.DataFrame:
    """
    The availability periods of resources, for a table

    :param df: Resource dataframe, one row per period
    :type df: pd.DataFrame
    :return: Dataframe with resource, start, end and availability
    :rtype: pd.DataFrame
    """

    d = df[["resource", "start", "end", "availability"]].copy()
    d["start"] = pd.to_datetime(d["start"])
    d["end"] = pd.to_datetime(d["end"])
    d["availability"] = d["availability"].apply(availability_text)
    return d.reset_index(drop=True)

def availability_gantt_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    Resource dataframe with hover text and bar opacity for the availability Gantt

    Bars are faded in proportion to availability, so a period of leave at 0% is faint and
    a period at 50% is part way between. A period with no start is drawn from the earliest
    start of any resource, so it still has a bar.

    :param df: Resource dataframe, one row per period
    :type df: pd.DataFrame
    :return: Copy of the dataframe with _hover and _opacity columns
    :rtype: pd.DataFrame
    """

    d = df.copy()
    d["start"] = pd.to_datetime(d["start"])
    d["end"] = pd.to_datetime(d["end"])
    d["_hover"] = [f"Available {availability_text(a)}" + ("<br>No start date given" if pd.isna(s) else "")
                   for a, s in zip(d["availability"], d["start"], strict=True)]
    d["_opacity"] = [0.2 + 0.8 * a / 100 for a in d["availability"].astype(float)]
    d["start"] = d["start"].fillna(earliest_start())
    return d

def earliest_start() -> pd.Timestamp:
    """
    Earliest start date of any resource, used to draw periods that have no start

    :return: Earliest start, or today if no resource has a start date
    :rtype: pd.Timestamp
    """

    index = containers.get("resources", {}).get("index")
    if index is not None and index.imported_df is not None:
        start = pd.to_datetime(index.imported_df["start"]).min()
        if pd.notna(start):
            return min(start, today)
    return today

def create_availability_chart(df : pd.DataFrame, scale : str, colors : dict=None) -> go.Figure:
    """
    Create a stacked bar showing how many resources are available over time.

    Each bar covers one period (month / quarter / year) and has one segment per resource that is
    available in that period. A segment is the resource's full time equivalent: the availability of
    each of their periods, weighted by the fraction of the bar's period it covers. So a resource at
    100% for the whole month is 1.0, at 50% is 0.5, and one on leave for half the month is 0.5.
    The bar height is the full time equivalent number of resources. Resources with no end date
    are treated as available to the same horizon as the Gantt charts.

    :param df: Resource dataframe with resource, start, end and availability columns
    :type df: pd.DataFrame
    :param scale: One of SCALES
    :type scale: str
    :param colors: Optional dictionary of resource to colour, so colours match other charts
    :type colors: dict
    :return: Figure
    :rtype: go.Figure
    """

    freq, x_label, tick_format, hover_format = SCALES[scale]

    d = df[["resource", "start", "end", "availability"]].copy()
    d["start"] = pd.to_datetime(d["start"], errors="coerce")
    d["end"] = pd.to_datetime(d["end"], errors="coerce")
    d["availability"] = d["availability"].astype(float)

    horizon = max(d["end"].max(), default_end_date) if d["end"].notna().any() else default_end_date
    d["start"] = d["start"].fillna(d["start"].min() if d["start"].notna().any() else min(today, horizon))

    # Periods covering the whole range
    first = d["start"].min().to_period(freq[0]).start_time
    periods = pd.date_range(first, horizon, freq=freq)

    # Periods with no end run to the end of the last bar, so that bar is counted in full rather than part counted
    day = pd.Timedelta(days=1)
    d["end"] = d["end"].fillna(periods[-1] + pd.tseries.frequencies.to_offset(freq) - day)

    # Add up each resource's share of a full time person in each bar
    rows = []
    for p in periods:
        p_end = p + pd.tseries.frequencies.to_offset(freq) - day
        days = (p_end - p) / day + 1
        fte = {}
        for r in d.itertuples():
            overlap = (min(r.end, p_end) - max(r.start, p)) / day + 1
            if overlap > 0:
                fte[r.resource] = fte.get(r.resource, 0) + overlap / days * r.availability / 100
        for resource, value in fte.items():
            if value > 0:
                rows.append({"period": p, "resource": resource, "available": round(value, 2)})

    plot_df = pd.DataFrame(rows, columns=["period", "resource", "available"])
    bar_width = {"Monthly" : 28, "Quarterly" : 50, "Yearly" : 90}[scale]

    fig = stacked_bar(
        plot_df,
        "",
        ("period", x_label),
        ("available", "Resources available (full time)"),
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
        text=[f"{round(v, 1):g}" for v in totals.values],
        textposition="top center",
        textfont=dict(size=12, color="#1c2433"),
        hoverinfo="skip",
        showlegend=False,
        cliponaxis=False,
        meta=INK,
    ))
    fig.update_yaxes(dtick=1, rangemode="tozero")

    return fig

def monthly_allocation(alloc : pd.DataFrame) -> pd.DataFrame:
    """
    How much of each resource's time is allocated in each month, one row per allocation and month

    Allocations are in whole months, so an allocation from 2026-01 to 2026-03 is in each of January, February and March.

    :param alloc: Imported workpackages dataframe, one row per allocation
    :type alloc: pd.DataFrame
    :return: Dataframe with resource, month (its first day), project, workpackage and allocation (1.0 = full time)
    :rtype: pd.DataFrame
    """

    columns = ["resource", "month", "project", "workpackage", "allocation"]
    if alloc is None or alloc.empty or "allocations.resource" not in alloc.columns:
        return pd.DataFrame(columns=columns)

    rows = []
    for r in alloc.to_dict("records"):
        start = pd.to_datetime(r.get("allocations.start"), errors="coerce")
        end = pd.to_datetime(r.get("allocations.end"), errors="coerce")
        if pd.isna(start) or pd.isna(end) or pd.isna(r.get("allocations.resource")):
            continue
        for m in pd.period_range(start.to_period("M"), end.to_period("M"), freq="M"):
            rows.append({"resource" : r["allocations.resource"], "month" : m.start_time, "project" : r.get("project"),
                         "workpackage" : r.get("workpackage"), "allocation" : float(r["allocations.allocation"])})
    return pd.DataFrame(rows, columns=columns)

def monthly_availability(df : pd.DataFrame, months) -> pd.DataFrame:
    """
    How much of each resource's time is available in each month

    A resource's availability in a month is the availability of each of their periods, weighted by the fraction of
    the month it covers: 100% for the whole month is 1.0, 50% is 0.5, and on leave for half the month is 0.5.
    A period with no start or no end runs from or to the end of time.

    :param df: Resource dataframe, one row per period
    :type df: pd.DataFrame
    :param months: First day of each month
    :return: Dataframe with resource, month and available (1.0 = full time), one row per resource and month
    :rtype: pd.DataFrame
    """

    start = pd.to_datetime(df["start"]).fillna(pd.Timestamp.min)
    end = pd.to_datetime(df["end"]).fillna(pd.Timestamp.max)
    share = df["availability"].astype(float) / 100
    day = pd.Timedelta(days=1)

    frames = []
    for m in months:
        m_end = m + pd.offsets.MonthEnd(0)
        overlap = ((end.clip(upper=m_end) - start.clip(lower=m)) / day + 1).clip(lower=0)
        fte = (overlap / m_end.day * share).groupby(df["resource"], sort=False).sum()
        frames.append(pd.DataFrame({"resource" : fte.index, "month" : m, "available" : fte.values}))
    if not frames:
        return pd.DataFrame(columns=["resource", "month", "available"])
    return pd.concat(frames, ignore_index=True)

def allocation_vs_availability() -> pd.DataFrame:
    """
    Every month in which each resource is allocated to any workpackage, with how much of their time is allocated and available

    Allocations to every project are added together. Resources that are allocated but not defined in the resources
    are left out, since there is nothing to check them against.

    :return: Dataframe with resource, month, allocated and available (1.0 = full time), and the projects and
             workpackages (sorted lists) the resource is allocated to that month
    :rtype: pd.DataFrame
    """

    columns = ["resource", "month", "allocated", "available", "projects", "workpackages"]
    resources = containers.get("resources", {}).get("index")
    wps = containers.get("workpackages", {}).get("index")
    if resources is None or resources.imported_df is None or resources.imported_df.empty or wps is None:
        return pd.DataFrame(columns=columns)

    # Every page of the report uses this, so it is worked out once
    if resources.allocation_check is not None:
        return resources.allocation_check

    m = monthly_allocation(wps.imported_df)
    m = m[m["resource"].isin(set(resources.imported_df["resource"]))]
    if m.empty:
        resources.allocation_check = pd.DataFrame(columns=columns)
        return resources.allocation_check

    used = m.groupby(["resource", "month"], as_index=False).agg(
        allocated=("allocation", "sum"),
        projects=("project", lambda x: sorted(set(x.dropna()))),
        workpackages=("workpackage", lambda x: sorted(set(x.dropna()))),
    )
    available = monthly_availability(resources.imported_df, sorted(used["month"].unique()))
    used = used.merge(available, on=["resource", "month"], how="left")
    used["available"] = used["available"].fillna(0.0)
    resources.allocation_check = used[columns].sort_values(["resource", "month"]).reset_index(drop=True)
    return resources.allocation_check

def percent(value : float) -> str:
    """ A fraction of full time as a percentage, e.g. 1.25 is 125% """
    return f"{100 * value:.0f}%"

def over_allocation(project : (str | None) = None, resource : (str | None) = None) -> pd.DataFrame:
    """
    The months in which resources are allocated more of their time than they have available

    Consecutive months of a resource with the same allocation, availability and workpackages are one row.

    :param project: Only months in which the resource is allocated to this project
    :type project: str | None
    :param resource: Only this resource
    :type resource: str | None
    :return: Dataframe with resource, from, to, months, time available, time allocated, over allocated (html), project and
             workpackage (comma separated names), one row per run of months, worst first
    :rtype: pd.DataFrame
    """

    columns = ["resource", "from", "to", "months", "time available", "time allocated", "over allocated", "project", "workpackage"]
    d = allocation_vs_availability()
    d = d[d["allocated"] > d["available"] + 1e-6]
    if project is not None:
        d = d[d["projects"].map(lambda x: project in x)]
    if resource is not None:
        d = d[d["resource"] == resource]
    if d.empty:
        return pd.DataFrame(columns=columns)

    # Runs of consecutive months that are the same
    d = d.assign(_projects=d["projects"].map(", ".join), _workpackages=d["workpackages"].map(", ".join),
                 _allocated=d["allocated"].round(6), _available=d["available"].round(6)).reset_index(drop=True)
    same = ["resource", "_allocated", "_available", "_projects", "_workpackages"]
    previous = d.shift()
    new_run = (d[same] != previous[same]).any(axis=1) | (d["month"] != previous["month"] + pd.DateOffset(months=1))
    d["_run"] = new_run.cumsum()

    runs = d.groupby("_run", as_index=False).agg(
        resource=("resource", "first"),
        start=("month", "min"),
        end=("month", "max"),
        months=("month", "size"),
        available=("available", "first"),
        allocated=("allocated", "first"),
        project=("_projects", "first"),
        workpackage=("_workpackages", "first"),
    )
    runs["_over"] = runs["allocated"] - runs["available"]
    runs = runs.sort_values(["_over", "months"], ascending=False)

    def over_text(r):
        if r.available <= 1e-6:
            return '<span class="badge badge-over">NOT AVAILABLE</span>'
        return f'<span class="badge badge-over">+{percent(r.allocated - r.available)}</span>'

    return pd.DataFrame({
        "resource" : runs["resource"],
        "from" : runs["start"].dt.strftime("%Y-%m"),
        "to" : runs["end"].dt.strftime("%Y-%m"),
        "months" : runs["months"],
        "time available" : runs["available"].map(percent),
        "time allocated" : runs["allocated"].map(percent),
        "over allocated" : [over_text(r) for r in runs.itertuples()],
        "project" : runs["project"],
        "workpackage" : runs["workpackage"],
    }).reset_index(drop=True)

OVER_ALLOCATION_HELP = ("Months in which a resource is allocated more of their time than they have available, adding up their "
                        "allocations to every workpackage of every project. Available is their availability that month, weighted "
                        "by how much of the month each availability period covers, so a week of leave takes about a quarter off. "
                        "Allocated and available are percentages of full time. Consecutive months that are the same are shown "
                        "as one row, from the first month to the last. NOT AVAILABLE means the resource has no availability "
                        "that month at all, for example before they start or after they leave.")
""" Hover guidance for the over allocation tables """

def add_over_allocation(tab, project : (str | None) = None, resource : (str | None) = None) -> None:
    """
    Add the table of over allocated months to a tab, or a line saying there are none

    :param tab: Tab of a page
    :param project: Only months in which the resource is allocated to this project
    :type project: str | None
    :param resource: Only this resource
    :type resource: str | None
    :return: None
    """

    over = over_allocation(project=project, resource=resource)
    if over.empty:
        if resource is not None:
            text = "This resource is never allocated more of their time than they have available."
        elif project is not None:
            text = "No resource is allocated more of their time than they have available in any month they work on this project."
        else:
            text = "No resource is allocated more of their time than they have available in any month."
        tab.add_paragraph("Over Allocation", text, help=OVER_ALLOCATION_HELP)
    else:
        tab.add_table("Over Allocation", over, help=OVER_ALLOCATION_HELP)

def create_allocation_heatmap() -> (go.Figure | None):
    """
    Heatmap of how much of each resource's available time is allocated, by month

    Each cell is the resource's allocation as a percentage of their availability that month. Blue is within it,
    getting darker as it fills, and red is over it. Months in which a resource is allocated but has no availability
    are drawn at the top of the scale, the darkest red. Months with no allocation are blank.

    :return: Figure, or None if no resource is allocated
    :rtype: go.Figure | None
    """

    d = allocation_vs_availability()
    if d.empty:
        return None

    resources = list(dict.fromkeys(containers["resources"]["index"].imported_df["resource"]))
    resources = [r for r in resources if r in set(d["resource"])]
    months = pd.date_range(d["month"].min(), d["month"].max(), freq="MS")

    top = 200.0
    z = np.full((len(resources), len(months)), np.nan)
    text = np.full((len(resources), len(months)), "", dtype=object)
    row = {r : i for i, r in enumerate(resources)}
    col = {m : j for j, m in enumerate(months)}
    for r in d.itertuples():
        i, j = row[r.resource], col[r.month]
        if r.available <= 1e-6:
            z[i, j] = top
            share = "No availability"
        else:
            z[i, j] = min(100 * r.allocated / r.available, top)
            share = f"{r.allocated / r.available:.0%} of the time available"
        text[i, j] = (f"Allocated {percent(r.allocated)}, available {percent(r.available)}<br>{share}"
                      f"<br>{', '.join(r.workpackages)}")

    # Blue up to 100%, then red
    edge = 100 / top
    colorscale = [[0.0, "#EEF0FE"], [edge, "#636EFA"], [edge + 1e-6, "#F4A3A8"], [1.0, "#D62839"]]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=months,
        y=resources,
        zmin=0,
        zmax=top,
        colorscale=colorscale,
        xgap=2,
        ygap=2,
        customdata=text,
        hovertemplate="<b>%{y}</b> %{x|%b %Y}<br>%{customdata}<extra></extra>",
        colorbar=dict(title=dict(text="% of available"), ticksuffix="%", tickvals=[0, 50, 100, 150, 200],
                      ticktext=["0", "50", "100", "150", "200+"]),
    ))
    style_axes(fig)
    fig.update_xaxes(title="Month", tickformat="%b<br>%Y", dtick="M3")
    fig.update_yaxes(title="Resource", autorange="reversed")
    fig.update_layout(height=max(len(resources) * 40 + 160, 300), margin=dict(l=50, r=50, t=40, b=50),
                      meta={"link_key" : "resource"})
    return fig

ALLOCATION_HEATMAP_HELP = ("How much of each resource's available time is allocated in each month, adding up their allocations "
                           "to every project. Blue is within their availability, darker as it fills up; red is more than they "
                           "have available. A cell of 100% is fully allocated. The darkest red is 200% or more, or a month in "
                           "which they are allocated but not available at all. Blank months have no allocation. Hover for "
                           "the allocation, availability and workpackages, and click a row to open the resource page.")
""" Hover guidance for the allocation heatmap """

PERIODS_HELP = ("Each period the resource is available, and the percentage of their time available in it. "
                "Time between periods, for example leave, is time the resource is not available. An empty end "
                "means the period is open ended.")
""" Hover guidance for the table of availability periods """

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

        df = self.imported_df

        # Use the colour this resource has on the overview page
        index = containers.get("resources", {}).get("index")
        colors = color_map(index.imported_df["resource"]) if index is not None and index.imported_df is not None else None

        # Add availability gantt, one bar per period
        tab = self.html.add_tab("Availability")
        tab.add_chart("Availability", gantt(
                                                availability_gantt_df(df),
                                                "",
                                                ("start", "Start Date"),
                                                ("end", "End Date"),
                                                ("resource", "Resource Name"),
                                                markers={"Today" : today},
                                                description="_hover",
                                                link_key="resource",
                                                colors=colors,
                                                opacity="_opacity",
                                            )
        )
        tab.add_table("Availability Periods", period_table(df), help=PERIODS_HELP)

        self.add_allocations()
        self.add_tasks()

        # Add details table
        tab = self.html.add_tab("Details")
        tab.add_table("Resource Details", resource_summary(df), transpose=True,
                      help="Definition of this resource as given in the resources input file. Start and end are the first "
                           "and last dates of its availability periods, and available today is its availability now.")

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

        # Their availability over the same months as the charts, which pad the allocations by two months each side
        months = pd.date_range((start.min() - pd.DateOffset(months=2)).to_period("M").start_time,
                               (end.max() + pd.DateOffset(months=2)).to_period("M").start_time, freq="MS")
        available = monthly_availability(self.imported_df, months)

        available_help = (" The dashed line is the effort the resource has available in each period: their availability, "
                          "weighted by how much of the period each availability period covers. Bars above the line are "
                          "over allocated.")
        tab = self.html.add_tab("Allocations")
        tab.add_chart("Allocation by Project", create_allocation_chart(a, "project", available=available),
                      help="Effort allocated to this resource each period, stacked by project. "
                           "Click a segment to open the project page." + available_help)
        tab.add_chart("Allocation by Workpackage", create_allocation_chart(a, "workpackage", available=available),
                      help="Effort allocated to this resource each period, stacked by workpackage. "
                           "Click a segment to open the workpackage page." + available_help)
        add_over_allocation(tab, resource=self.name)
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
        if index is None or index.imported_df is None or "resources" not in index.imported_df.columns:
            return

        # Tasks shared by several people are shown, in full, on the page of each of them
        t = index.imported_df
        t = t[t["resources"].map(lambda r: self.name in r)]
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
        tab.add_table("Tasks", task_summary_table(t), units=True,
                      help="Progress of every task this resource is associated with. A task shared with other people is "
                           "shown in full: its effort is that of everyone working on it. Remaining of 0 means the task "
                           "is complete. " + TASK_ESTIMATE_HELP)
        add_over_estimate(tab, t)

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

        self.allocation_check = None
        """ Result of allocation_vs_availability, once it has been worked out """

    def import_data(self, definitions : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param definitions: List of dictionaries
        :return: None
        """

        self.check_definitions(definitions, "resource")
        self.validate_data(pd.DataFrame(definitions), pd.DataFrame(columns=FIELDS))

        # One row per availability period
        rows = []
        for d in definitions:
            for p in resource_periods(d):
                rows.append({"resource" : d["resource"], "uname" : d.get("uname"), **p, "profile" : d.get("profile")})

        self.imported_df = pd.DataFrame(rows, columns=COLUMNS)
        self.imported_df["start"] = pd.to_datetime(self.imported_df["start"])
        self.imported_df["end"] = pd.to_datetime(self.imported_df["end"])
        self.imported_df["availability"] = self.imported_df["availability"].astype(float)

        # Create child resources
        for d in definitions:
            name = d["resource"]
            self.children[name] = Resource(name, self.path)
            self.children[name].imported_df = self.imported_df[self.imported_df["resource"] == name].reset_index(drop=True)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        df = self.imported_df

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
                                                        availability_gantt_df(df),
                                                        "",
                                                        ("start", "Start Date"),
                                                        ("end", "End Date"),
                                                        ("resource", "Resource Name"),
                                                        markers={"Today" : today},
                                                        link_key="resource",
                                                        description="_hover",
                                                        colors=colors,
                                                        opacity="_opacity",
                                                    )
        )

        # Add stacked availability chart, with a choice of scale
        tab.add_scaled_chart("Resources Available Over Time",
                             {scale : create_availability_chart(df, scale, colors) for scale in SCALES},
                             label="Scale",
                             help="Number of full time resources available in each period. Each coloured segment is one "
                                  "resource: its availability weighted by how much of the period it covers, so a resource "
                                  "at 50% counts 0.5 and one on leave for half a month counts 0.5 for that month. The bar "
                                  "height (also printed above the bar) is the full time equivalent number of resources. "
                                  "Resources with no end date are assumed available to the end of the Gantt chart above. "
                                  "Click a segment to open that resource's page.")

        # How much of their available time each resource is allocated
        tab = self.html.add_tab("Allocation")
        heatmap = create_allocation_heatmap()
        if heatmap is None:
            tab.add_paragraph("Allocation", "No resource is allocated to a workpackage.", help=ALLOCATION_HEATMAP_HELP)
        else:
            tab.add_chart("Allocation of Available Time", heatmap, help=ALLOCATION_HEATMAP_HELP)
        add_over_allocation(tab)

        # Add table to html
        tab = self.html.add_tab("Resources")
        tab.add_table("Resources", resource_summary(df),
                      help="All resources. Start and end are the first and last dates of each resource's availability "
                           "periods, and available today is their availability now. Click a name to open the resource page.")
        tab.add_table("Availability Periods", period_table(df), help=PERIODS_HELP)

        super().export_html()

__all__ = [
    "Resources",
    "monthly_allocation",
    "monthly_availability",
    "allocation_vs_availability",
    "over_allocation",
    "add_over_allocation",
    "create_allocation_heatmap",
]
