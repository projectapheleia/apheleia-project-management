"""
Burn charts: the burndown (effort remaining) and burnup (effort spent against the total) of a set of tasks,
with a forecast of when the remaining effort will be done based on the resources allocated to it
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ._charts import INK, LEGEND_OUTSIDE, base_layout
from ._containers import containers
from ._utils import today

REMAINING_COLOR = "#636EFA"
""" Colour of the effort remaining on the burndown """

SPENT_COLOR = "#00A67E"
""" Colour of the effort spent on the burnup """

ESTIMATE_COLOR = "#E8762C"
""" Colour of the original estimate on the burnup """

MARKER_COLOR = "#d62839"
""" Colour of the date markers (today, planned end), as on the timelines """

END_COLOR = "#8E44AD"
""" Colour of the estimated end date marker """

MARKER_ROW_HEIGHT = 16
""" Vertical step between rows of marker labels in pixels """

NO_WORKPACKAGE = "(no workpackage)"
""" Name the forecast gives the tasks that have no workpackage """

ALLOCATION_COLUMNS = ["start", "end", "allocation"]
""" Columns of an allocation table: first month, last month (inclusive) and fraction of full time """

BURN_HELP = ("The burndown shows the effort remaining over time and the burnup the effort spent against the total "
             "(spent + remaining), added up over the tasks from their status updates. A task is counted from its first "
             "status update, so the total steps up when work is added. While work remains, the dashed lines are a linear "
             "forecast from the latest status (or today, if that is later and the report has a date) at the rate the resources are allocated: an "
             "allocation of 1.0 does one day of effort every working day, so the forecast is a straight line through each "
             "period of allocation and flat where nothing is allocated. Each workpackage is forecast at the rate of its own "
             "allocation, and a task at an equal share of its resources' allocation to its workpackage with their other "
             "unfinished tasks there. The estimated end date is the working day the allocated effort first covers the "
             "effort remaining. If the allocation runs out first, the forecast carries on at the average allocated rate "
             "and the end date is marked as beyond the allocation.")
""" Hover guidance shared by the burn charts and their summary """


def _months(df : pd.DataFrame, start : str, end : str, allocation : str) -> pd.DataFrame:
    """
    Allocation table from workpackage allocations

    :param df: Dataframe of workpackage allocations
    :param start: Column of the first month
    :param end: Column of the last month
    :param allocation: Column of the fraction of full time
    :return: Dataframe with ALLOCATION_COLUMNS
    """

    if df is None or df.empty:
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)
    return pd.DataFrame({
        "start" : pd.to_datetime(df[start]).dt.to_period("M"),
        "end" : pd.to_datetime(df[end]).dt.to_period("M"),
        "allocation" : df[allocation].astype(float),
    }).reset_index(drop=True)

def workpackage_allocation(names) -> pd.DataFrame:
    """
    Every allocation of a set of workpackages

    :param names: Names of the workpackages
    :return: Dataframe with ALLOCATION_COLUMNS
    """

    frames = [containers.get("workpackage", {})[n].imported_df for n in names if n in containers.get("workpackage", {})]
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)
    return _months(pd.concat(frames, ignore_index=True), "allocations.start", "allocations.end", "allocations.allocation")

def task_allocation(task_df : pd.DataFrame) -> pd.DataFrame:
    """
    Allocation working on a task. Each resource of the task gives it an equal share of their allocation to the task's
    workpackage, shared with the other unfinished tasks they have in that workpackage

    :param task_df: Dataframe of the status updates of one task
    :return: Dataframe with ALLOCATION_COLUMNS
    """

    latest = task_df.sort_values("status.date").iloc[-1]
    wp = containers.get("workpackage", {}).get(latest["workpackage"])
    index = containers.get("tasks", {}).get("index")
    if wp is None or wp.imported_df is None or index is None:
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)

    every = index.imported_df[index.imported_df["workpackage"] == latest["workpackage"]]
    unfinished = every.sort_values("status.date").groupby("task").last()
    unfinished = unfinished[unfinished["status.remaining"] > 0]

    frames = []
    for resource in latest["resources"]:
        share = max(sum(resource in r for r in unfinished["resources"]), 1)
        alloc = wp.imported_df[wp.imported_df["allocations.resource"] == resource]
        frames.append(alloc.assign(**{"allocations.allocation" : alloc["allocations.allocation"].astype(float) / share}))

    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)
    return _months(pd.concat(frames, ignore_index=True), "allocations.start", "allocations.end", "allocations.allocation")

def burn_history(tasks_df : pd.DataFrame) -> pd.DataFrame:
    """
    Effort spent and remaining of a set of tasks at each status update. Each task keeps the values of its latest
    update until its next one, and counts nothing before its first

    :param tasks_df: Dataframe of task status updates
    :return: Dataframe indexed by date with spent, remaining and total (spent + remaining) columns, in days
    """

    d = tasks_df.assign(**{"status.date" : pd.to_datetime(tasks_df["status.date"])})
    pivot = d.groupby(["status.date", "task"])[["status.spent", "status.remaining"]].last().unstack("task")
    pivot = pivot.sort_index().ffill().fillna(0).astype(float)
    history = pd.DataFrame({
        "spent" : pivot["status.spent"].sum(axis=1),
        "remaining" : pivot["status.remaining"].sum(axis=1),
    })
    history["total"] = history["spent"] + history["remaining"]
    return history

def forecast(remaining : float, start : pd.Timestamp, allocation : pd.DataFrame) -> dict:
    """
    Forecast how the remaining effort is done, at the rate the resources are allocated

    Each working day after start does effort equal to the allocations covering its month (1.0 is one day of effort a
    day), so the forecast is a straight line through each period of allocation and flat where nothing is allocated.
    The end is the first working day the effort done reaches the effort remaining. If the allocations end first, the
    rest is done at the average rate from start to the end of the allocations.

    :param remaining: Effort remaining in days
    :param start: Date the forecast starts from
    :param allocation: Dataframe with ALLOCATION_COLUMNS
    :return: Dictionary with done (Series of the effort done by the end of each working day, at most remaining; empty
             if nothing is allocated), end (Timestamp, or NaT if nothing is allocated), within (whether the end is within
             the allocations) and allocation_end (last day allocated, or NaT)
    """

    nothing = {"done" : pd.Series(dtype=float), "end" : pd.NaT, "within" : False, "allocation_end" : pd.NaT}
    if allocation is None or allocation.empty:
        return nothing

    allocation_end = allocation["end"].max().end_time.normalize()
    nothing["allocation_end"] = allocation_end
    days = pd.bdate_range(start + pd.Timedelta(days=1), max(allocation_end, start))
    if len(days) == 0:
        return nothing

    months = days.to_period("M")
    capacity = np.zeros(len(days))
    for r in allocation.itertuples():
        capacity += np.where((months >= r.start) & (months <= r.end), r.allocation, 0.0)

    done = np.cumsum(capacity)
    if done[-1] <= 0:
        return nothing

    reached = np.flatnonzero(done >= remaining - 1e-9)
    if len(reached):
        i = reached[0]
        return {"done" : pd.Series(np.minimum(done[:i + 1], remaining), index=days[:i + 1]), "end" : days[i],
                "within" : True, "allocation_end" : allocation_end}

    # Beyond the allocation: carry on at the average allocated rate
    rate = done[-1] / len(days)
    extra = int(np.ceil((remaining - done[-1]) / rate - 1e-9))
    more = pd.bdate_range(days[-1] + pd.Timedelta(days=1), periods=extra)
    done = np.concatenate([done, np.minimum(done[-1] + rate * np.arange(1, extra + 1), remaining)])
    return {"done" : pd.Series(done, index=days.append(more)), "end" : more[-1], "within" : False,
            "allocation_end" : allocation_end}

def combined_forecast(tasks_df : pd.DataFrame, allocations : dict, start : pd.Timestamp) -> dict:
    """
    Forecast of a set of tasks. The effort remaining of each workpackage is forecast at the rate of its own allocation,
    and the effort done added up, so that people allocated to one workpackage do not do the work of another

    :param tasks_df: Dataframe of task status updates
    :param allocations: Dictionary of workpackage name to its allocation (Dataframe with ALLOCATION_COLUMNS)
    :param start: Date the forecast starts from
    :return: Dictionary with done (Series of the effort done by each working day, added up over the workpackages),
             end (NaT if a workpackage with effort remaining has no allocation to do it), within, allocation_end and
             unallocated (names of the workpackages with effort remaining and no allocation)
    """

    # Tasks with no workpackage have no allocation to forecast them with
    wp = tasks_df["workpackage"] if "workpackage" in tasks_df.columns else pd.Series(np.nan, index=tasks_df.index)
    tasks_df = tasks_df.assign(workpackage=wp.fillna(NO_WORKPACKAGE))
    latest = tasks_df.sort_values("status.date").groupby("task").last()
    remaining = latest.groupby("workpackage")["status.remaining"].sum().astype(float)
    plans = {wp : forecast(r, start, allocations.get(wp)) for wp, r in remaining.items() if r > 0}

    unallocated = [wp for wp, f in plans.items() if pd.isna(f["end"])]
    ends = [f["end"] for f in plans.values() if pd.notna(f["end"])]
    curves = [f["done"] for f in plans.values() if not f["done"].empty]

    done = pd.Series(dtype=float)
    if curves:
        index = curves[0].index
        for c in curves[1:]:
            index = index.union(c.index)
        done = sum(c.reindex(index).ffill().fillna(0) for c in curves)

    allocation_ends = [f["allocation_end"] for f in plans.values() if pd.notna(f["allocation_end"])]
    return {
        "done" : done,
        "end" : max(ends) if ends and not unallocated else pd.NaT,
        "within" : all(f["within"] for f in plans.values()),
        "allocation_end" : max(allocation_ends) if allocation_ends else pd.NaT,
        "unallocated" : unallocated,
    }

def _corners(done : pd.Series) -> pd.Series:
    """
    The points of a forecast where its rate changes, which is all that is needed to draw it

    :param done: Effort done by each working day
    :return: The same series at its first and last days and the days either side of a change of rate
    """

    if len(done) < 3:
        return done
    step = np.diff(done.to_numpy())
    change = np.flatnonzero(np.abs(np.diff(step)) > 1e-9) + 1
    keep = np.unique(np.concatenate([[0, len(done) - 1], change]))
    return done.iloc[keep]

def _markers(markers : list) -> tuple[list, list]:
    """
    Vertical lines at dates, labelled above the plot. Labels are put on rows so that neighbours do not overlap

    :param markers: List of (label, date, color, dash)
    :return: Layout shapes and annotations
    """

    items = sorted([m for m in markers if pd.notna(m[1])], key=lambda m: m[1])
    shapes, annotations = [], []
    for row, (label, date, color, dash) in enumerate(items):
        x = date.timestamp() * 1000
        shapes.append(dict(type="line", xref="x", yref="y domain", x0=x, x1=x, y0=0, y1=1,
                           line=dict(color=color, dash=dash, width=2)))
        annotations.append(dict(xref="x", yref="y domain", x=x, y=1, xanchor="left", yanchor="top", showarrow=False,
                                text=label, yshift=8 + row * MARKER_ROW_HEIGHT, font=dict(color=color, size=12)))
    return shapes, annotations

def _burn_chart(lines : list, markers : list, x_range : list) -> go.Figure:
    """
    A burn chart. The figure is built in one go from plain data, which is much quicker than adding to it a piece at
    a time, as plotly checks the whole figure on every change

    :param lines: List of (name, x, y, color, dash, meta) traces
    :param markers: List of (label, date, color, dash) vertical markers
    :param x_range: Dates the x axis spans
    :return: Figure
    """

    data = [dict(
                type="scatter", x=x, y=y, name=name, meta=meta,
                mode="lines+markers" if dash == "solid" else "lines",
                line=dict(color=color, width=2, dash=dash),
                marker=dict(size=8, color=color),
                hovertemplate=f"{name}: %{{y:.4~g}} days<extra></extra>",
            ) for name, x, y, color, dash, meta in lines]

    shapes, annotations = _markers(markers)
    layout = base_layout()
    layout["xaxis"].update(title=dict(text="Date"), range=x_range, tickformat="%d %b<br>%Y")
    layout["yaxis"].update(title=dict(text="Effort (Days)"), rangemode="tozero")
    layout.update(
        height=480,
        autosize=True,
        hovermode="x unified",
        margin=dict(l=50, r=50, t=30 + len(shapes) * MARKER_ROW_HEIGHT, b=50),
        legend=LEGEND_OUTSIDE,
        shapes=shapes,
        annotations=annotations,
    )
    return go.Figure(data=data, layout=layout)

def _date(value) -> str:
    return value.strftime("%Y-%m-%d") if pd.notna(value) else "-"

def _days(value : float) -> str:
    return f"{value:,.1f}".rstrip("0").rstrip(".")

def add_burnchart(tab, tasks_df : pd.DataFrame, allocations : dict, what : str, deadline : tuple=None) -> None:
    """
    Add a summary of progress and the forecast end date, a burndown and a burnup chart to a tab

    :param tab: Tab of a page
    :param tasks_df: Dataframe of the status updates of the tasks, or None if there are none
    :param allocations: Dictionary of workpackage name to the allocation doing its remaining effort (Dataframe with
                        ALLOCATION_COLUMNS), see combined_forecast
    :param what: What the tasks are, e.g. "project", for the text
    :param deadline: Optional (label, date) the work is planned to be done by, e.g. ("Project end", date)
    :return: None
    """

    if tasks_df is None or tasks_df.empty:
        tab.add_paragraph("Burnchart", f"No tasks have been recorded for this {what}, so there is no progress to chart.",
                          help=BURN_HELP)
        return

    history = burn_history(tasks_df)
    latest = history.iloc[-1]
    spent, remaining, total = float(latest["spent"]), float(latest["remaining"]), float(latest["total"])
    last_update = history.index.max()

    deadline_label, deadline_date = deadline if deadline is not None else (None, pd.NaT)
    deadline_date = pd.to_datetime(deadline_date) if deadline_date is not None else pd.NaT

    estimates = pd.to_numeric(tasks_df.groupby("task")["estimate"].first(), errors="coerce") \
        if "estimate" in tasks_df.columns else pd.Series(dtype=float)
    estimate = float(estimates.sum()) if len(estimates) and estimates.notna().all() else None

    # Forecast of the remaining effort, from the latest update or today if that is later
    now = today()
    start = max(now, last_update) if now is not None else last_update
    plan = combined_forecast(tasks_df, allocations, start) if remaining > 0 else None
    if plan is not None:
        end = plan["end"]
    else:
        # Complete: the end is when the remaining effort last became zero
        still = history.index[history["remaining"] > 0]
        end = history.index[history.index > still.max()].min() if len(still) else history.index.min()

    # Summary tiles
    pct = 100 * spent / total if total > 0 else 100.0
    if plan is None:
        tiles = [("Completed", _date(end))]
    elif pd.isna(end):
        tiles = [("Estimated end", "No allocation", True)]
    else:
        tiles = [("Estimated end", _date(end), not plan["within"])]
    tiles += [("Progress", f"{pct:.0f}%"), ("Days spent", _days(spent)), ("Days remaining", _days(remaining))]
    if plan is not None:
        tiles.append(("Allocation ends", _date(plan["allocation_end"]), pd.notna(end) and not plan["within"]))
    if deadline_label:
        tiles.append((deadline_label, _date(deadline_date), pd.notna(end) and pd.notna(deadline_date) and end > deadline_date))
    tiles.append(("Latest update", _date(last_update)))

    unallocated = ""
    if plan is not None and plan["unallocated"]:
        unallocated = f" No allocation: {', '.join(plan['unallocated'])}."
    summary_help = (f"Progress of the {what} and when it is forecast to end. Estimated end is the date the allocated effort "
                    f"covers the effort remaining; it is highlighted when that is beyond the allocation"
                    + (f" or after the {deadline_label.lower()}" if deadline_label else "")
                    + ". No allocation means a workpackage with effort remaining has no resources allocated after the "
                      "forecast starts, so the end cannot be forecast." + unallocated + " " + BURN_HELP)
    tab.add_summary("Burn Summary", tiles, help=summary_help)

    # Forecast lines: flat from the latest update to the start of the forecast, then following the allocation
    fx, done = [], []
    if plan is not None and not plan["done"].empty:
        corners = _corners(plan["done"])
        fx = [last_update] + ([start] if start > last_update else []) + list(corners.index)
        done = [0.0] * (len(fx) - len(corners)) + list(corners.to_numpy())
    forecast_end = fx[-1] if fx else pd.NaT

    # Range of the charts: from the first update to the last date of interest
    marker_dates = [d for d in (end, forecast_end, deadline_date, now) if d is not None and pd.notna(d)]
    first = min([history.index.min()] + marker_dates)
    last = max([last_update] + marker_dates)
    pad = max((last - first) * 0.03, pd.Timedelta(days=3))
    x_range = [first - pad, last + pad]

    markers = [("Today", now, MARKER_COLOR, "dash")] if now is not None else []
    if deadline_label and pd.notna(deadline_date):
        markers.append((deadline_label, deadline_date, MARKER_COLOR, "dot"))
    if pd.notna(end):
        name = "Completed" if plan is None else "Estimated end" + ("" if plan["within"] else " (beyond allocation)")
        markers.append((f"{name} {_date(end)}", end, END_COLOR, "dashdot"))

    done = np.array(done)
    down = [("Remaining", history.index, history["remaining"], REMAINING_COLOR, "solid", None)]
    up = [("Spent", history.index, history["spent"], SPENT_COLOR, "solid", None),
          ("Total (spent + remaining)", history.index, history["total"], "#1c2433", "solid", INK)]
    if fx:
        down.append(("Forecast remaining", fx, remaining - done, REMAINING_COLOR, "dash", None))
        up.append(("Forecast spent", fx, spent + done, SPENT_COLOR, "dash", None))
        up.append(("Forecast total", [last_update, fx[-1]], [total, total], "#1c2433", "dash", INK))
    if estimate is not None:
        up.append(("Estimate", x_range, [estimate, estimate], ESTIMATE_COLOR, "dot", None))

    tab.add_chart("Burndown", _burn_chart(down, markers, x_range),
                  help=f"Effort remaining on the {what}'s tasks over time. The solid line is from the status updates; the "
                       "dashed line is the forecast to the estimated end date. " + BURN_HELP)
    tab.add_chart("Burnup", _burn_chart(up, markers, x_range),
                  help=f"Effort spent on the {what}'s tasks over time, against the total effort (spent + remaining). The "
                       "gap between them is the effort remaining. The dashed lines are the forecast to the estimated end "
                       "date. The Estimate line is the original estimates of the tasks added up, shown only when every "
                       "task has one. " + BURN_HELP)

__all__ = [
    "add_burnchart",
    "burn_history",
    "combined_forecast",
    "forecast",
    "task_allocation",
    "workpackage_allocation",
]
