import html as _html
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import _format
from ._utils import today_text, value_to_filename

COLUMN_HELP = {
    "task": "Name of the task - the smallest unit of tracked work.",
    "project": "The project this item belongs to. Click the link to open the project page.",
    "workpackage": "The workpackage (a group of related tasks and resource allocations) this item belongs to.",
    "resource": "The person (or team) doing the work. A task can be shared by several people.",
    "resources": "All resources allocated to this workpackage.",
    "milestone": "Milestone identifier. Milestones are shared checkpoints (e.g. M3) that projects give dates to.",
    "description": "Free-text description of the item.",
    "milestone range": "The date the workpackage must end by, which is the date of its milestone in the project. Starting earlier is fine.",
    "milestone check": "Whether the workpackage ends by its milestone, to the month. OUTSIDE MILESTONE says why it does not. Empty means no milestone was given.",
    "estimate check": "Whether the effort is within the estimate. For a workpackage it is the effort allocated, for a task the effort spent plus remaining. OVER ESTIMATE says by how much it is over. No estimate means there is nothing to check.",
    "check": "Whether the workpackage passes this check, and if not why. See the guidance on the table.",
    "problem": "What is wrong with the workpackage or task.",
    "start": "Planned start date (YYYY-MM-DD). For workpackage allocations this is the first allocated month. For tasks, a note in brackets shows the date was not given and defaults to the previous milestone.",
    "end": "Planned end date (YYYY-MM-DD). Empty means open-ended - charts extend these bars to the default horizon.",
    "date": "Date the milestone is planned to be reached (YYYY-MM-DD).",
    "uname": "Short user name / login of the resource.",
    "profile": "Link to further information about the resource.",
    "effort": "Total allocated effort, summed over all allocation periods. Shown in the unit chosen in the Units box (default man-months).",
    "allocated": "Total effort allocated to the workpackage (allocation x months, over all its allocations), in the unit chosen in the Units box.",
    "status.date": "Date of the status update (YYYY-MM-DD). The most recent update is the current position.",
    "status.spent": "Effort already spent on the task, as of the status date.",
    "status.remaining": "Estimated effort still required to complete the task. 0 means complete.",
    "current for": "Projects for which this is the current milestone, i.e. the next one due.",
    "next due": "Earliest date of this milestone among the projects it is current for.",
    "when": "Whether the milestone has passed, is the current milestone (the next one due), or is still upcoming.",
    "over estimate": "Tasks (and effort) that are past their estimate, i.e. spent plus remaining effort is more than the estimate.",
    "over by": "Effort by which spent plus remaining exceeds the estimate, in the unit chosen in the Units box.",
    "% over": "Over-run as a percentage of the estimate.",
    "estimate": "Original effort estimate, in the unit chosen in the Units box. For a task MISSING means none was provided; for a workpackage empty means none was given.",
    "variance": "Spent plus remaining effort minus the estimate, in the unit chosen in the Units box. Positive means the task is expected to overrun.",
    "no estimate": "Number of these tasks that have no estimate.",
    "tasks": "Number of tasks needed by this milestone: those forecast to finish on or before its date (and after the previous milestone).",
    "complete": "Tasks with no work remaining.",
    "in progress": "Tasks with some work spent and some remaining.",
    "not started": "Tasks with no work spent yet.",
    "spent": "Effort already spent on the task as of the latest status update, in the unit chosen in the Units box.",
    "remaining": "Estimated effort still required, in the unit chosen in the Units box. 0 means the task is complete.",
    "% complete": "Spent effort as a percentage of spent plus remaining effort.",
    "status": "Complete (nothing remaining), In progress, or Not started (nothing spent yet).",
    "last_status": "Date of the latest status update for the task.",
    "forecast_end": "Forecast completion: latest status date (not earlier than today for unfinished tasks, if the report has a date) plus the remaining working days.",
    "availability": "Percentage of the resource's time available in this period (100% = full time). Defaults to 100% if not given.",
    "available today": "Percentage of the resource's time available today. 0% (no active period) if today is outside all of their availability periods, e.g. they have left, not yet started or are between periods.",
    "available at latest update": "Percentage of the resource's time available on the date of the latest status update in the input, as the report has no date. 0% (no active period) if that date is outside all of their availability periods.",
    "periods": "Number of availability periods given for the resource.",
    "allocations.start": "First month of this resource allocation.",
    "allocations.end": "Last month of this resource allocation.",
    "allocations.resource": "Resource that is allocated.",
    "allocations.allocation": "Fraction of a resource's time allocated per month (1.0 = full time).",
    "update check": "How long ago the task's latest status update was. STALE means an unfinished task has gone longer than stale_days (in the format) without an update, so its progress and forecast may be out of date.",
    "days since update": "Calendar days from the task's latest status update to the day the report was made.",
    "stale": "Unfinished tasks whose latest status update is more than stale_days (in the format) old.",
    "task check": "Whether the tasks of the workpackage fit within it. TASKS OVER ALLOCATION means they need more effort (spent + remaining) than is allocated; TASKS OVER ESTIMATE means their estimates add up to more than the workpackage estimate.",
    "task estimates": "Original estimates of the workpackage's tasks added together, in the unit chosen in the Units box. Tasks with no estimate add nothing.",
    "task forecast": "Effort spent plus effort remaining of the workpackage's tasks added together: what the tasks are now expected to need, in the unit chosen in the Units box.",
    "task spent": "Effort already spent on the workpackage's tasks, in the unit chosen in the Units box.",
    "from": "First month (YYYY-MM) of this run of over allocated months.",
    "to": "Last month (YYYY-MM) of this run of over allocated months.",
    "months": "Number of months: those of the allocation, or of the run of over allocated months.",
    "time available": "Percentage of full time the resource is available in each of these months, weighted by how much of the month their availability periods cover.",
    "time allocated": "Percentage of full time the resource is allocated in each of these months, adding up their allocations to every workpackage of every project.",
    "over allocated": "How much more of their time the resource is allocated than they have available, as a percentage of full time.",
}
""" Help text shown when hovering over table column headers """

SECTION_HELP = {
    "availability": "Availability of the resource over time. Each bar is one availability period, from its start date to its end date; "
                    "a period with no end date runs to the default horizon. Bars are faded in proportion to availability, so "
                    "a period at 0% is faint; gaps between bars are times the resource is not available. Hover for the percentage. "
                    "The dashed red line marks today, if the report has a date.",
    "resource availability": "Availability of each resource over time. Each bar is one availability period, from its start date to its end date; "
                             "a period with no end date runs to the default horizon. Bars are faded in proportion to availability, so "
                             "a period at 0% is faint; gaps between bars are times the resource is not available. Hover for the percentage. "
                             "The dashed red line marks today, if the report has a date.",
    "task timeline": "Gantt chart of tasks. A bar starts at the first status update and ends at the forecast completion date "
                     "(latest status date plus the remaining effort in working days). Incomplete tasks are never forecast to end before today, if the report has a date.",
    "project timeline": "Planned duration of the project. Milestones are marked in red and labelled with their identifier: a dashed line is a milestone "
                        "with a due date only, and a dotted line at each end joined across the top is a milestone window, due on its end date.",
    "project timelines": "Planned duration of every project. Bars span start to end date; projects without an end date run to the default horizon.",
    "workpackage timeline": "Gantt chart of the workpackages in this project, spanning the earliest to latest resource allocation.",
    "workpackage timelines": "Gantt chart of workpackages, spanning the earliest to latest resource allocation in each.",
    "workpackage allocations": "Monthly resource allocation stacked by contributor. A value of 1.0 is one person working full time for the month.",
    "milestones": "Milestones and the dates they are planned for. Dates come from the project definition.",
    "resources": "All resources with the first and last dates they are available. Click a name to open the resource page.",
    "projects": "All projects with their start and end dates. Click a name to open the project page.",
    "workpackages": "Workpackages with their overall dates and total allocated effort in person-months.",
    "tasks": "All tasks. Click a name to open the task page with its timeline and progress.",
}
""" Help text for charts / tables, keyed by lower case title """

INDEX_HELP = {
    "projects": "Overview of all projects.\nThe Timelines tab shows every project on one Gantt chart; the Projects tab lists them. Click a project to open its page.",
    "resources": "Overview of all resources.\nThe Availability tab shows when each resource can be used and how many are available over time; the Resources tab lists them. Click a resource to open its page.",
    "milestones": "Overview of all milestones.\nMilestones are shared checkpoints; each project gives them its own dates. Click a milestone to open its page.",
    "workpackages": "Overview of all workpackages.\nWorkpackages group tasks and resource allocations within a project. Click a workpackage to open its page.",
    "tasks": "Overview of all tasks.\nTasks are the smallest unit of tracked work. Click a task to open its page.",
}
""" Page level help for the overview page of each container type """

DETAIL_HELP = {
    "project": "A project: a planned piece of work with a start and end date and milestones. The Summary tab shows its status, the Timeline tab its dates and milestones, and the Burnchart tab its progress and forecast end date. Its workpackages are listed on the Workpackages tab.",
    "resource": "A resource: a person or team that work can be allocated to. The chart shows when they are available.",
    "milestone": "A milestone: a checkpoint shared by projects. Each project sets its own date for it.",
    "workpackage": "A workpackage: a group of tasks and resource allocations that delivers part of a project. The Summary tab shows its checks and task progress, the Timeline tab its dates and tasks, and the Burnchart tab its progress and forecast end date.",
    "task": "A task: the smallest unit of tracked work. The Summary tab shows its latest status, the Timeline tab its forecast timeline and the Burnchart tab its progress and forecast end date.",
}
""" Page level help for a page describing a single item """

TABLE_TIP = "Click a column heading to sort (click again to reverse). " \
            "Type in the box under a heading to filter that column. " \
            "Filters accept operators: > >= < <= (numbers), = != (exact), ^= (starts with), $= (ends with), ~= (regular expression)."
""" Interaction guidance appended to every table """

CHART_TIP = "Hover over a bar for details. Drag to zoom, double-click to reset, and use the toolbar (top right of the chart) to pan or save an image."
""" Interaction guidance appended to every chart """


def _tip(text : str) -> str:
    """ Return an escaped data-tip attribute """
    return f' data-tip="{_html.escape(text, quote=True)}"'


def _info_badge(text : str) -> str:
    """ Return a keyboard focusable (i) badge that shows text on hover """
    return f'<span class="info-badge" tabindex="0" role="note" aria-label="{_html.escape(text, quote=True)}"{_tip(text)}>i</span>'


EARLY_JS = r"""
// Apply the saved theme before the page is drawn, so there is no flash of the wrong theme
(function () {
    var theme = null;
    try { theme = localStorage.getItem('apheleia-theme'); } catch (e) {}
    if (!theme && window.name.indexOf('apheleia-theme=') === 0) theme = window.name.slice(15);
    var known = __THEME_NAMES__;
    if (known.indexOf(theme) < 0) theme = __DEFAULT_THEME__;
    document.documentElement.setAttribute('data-theme', theme);
})();
"""

CSS = r"""
:root { --radius: 10px; }

/* The themes (colours and fonts) are written here from the format, see _format.theme_css */
__THEMES_CSS__

* { box-sizing: border-box; }

html, body {
    margin: 0;
    padding: 0;
    background: var(--page);
    color: var(--ink);
    font-family: var(--font);
    font-size: 14px;
    line-height: 1.45;
}

a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ---------- Page header ---------- */
.page-header {
    background: var(--header-bg);
    color: var(--on-dark);
    box-shadow: var(--header-shadow);
}
.page-header-inner {
    max-width: 1500px;
    margin: 0 auto;
    padding: 16px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
}
.page-kicker {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 11px;
    font-weight: 600;
    color: var(--kicker-text);
}
.page-title { margin: 2px 0 0 0; font-family: var(--title-font); font-size: 26px; font-weight: 600; letter-spacing: 0.01em; }
.page-meta { font-size: 12px; color: var(--meta-text); margin-top: 2px; }
.logo-link {
    display: block;
    background: var(--logo-bg);
    padding: 6px 12px;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}
.logo-link img, .logo-link svg { display: block; height: var(--logo-height, 44px); width: auto; max-width: 220px; filter: var(--logo-filter); }

/* ---------- Toolbar: always the first thing on a page ---------- */
.toolbar {
    position: sticky;
    top: 0;
    z-index: 900;
    background: var(--band-dark);
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}
.toolbar-inner {
    max-width: 1500px;
    margin: 0 auto;
    padding: 7px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}
.home-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 14px 4px 11px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.14);
    color: var(--on-dark);
    font-size: 13px;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.28);
    transition: background-color 0.15s;
}
.home-link:hover { background: rgba(255, 255, 255, 0.3); text-decoration: none; }
.theme-select { color: var(--toolbar-text); font-size: 13px; font-weight: 600; }
.theme-select select {
    margin-left: 6px;
    padding: 3px 8px;
    font: inherit;
    font-weight: 400;
    color: var(--on-dark);
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.28);
    border-radius: 5px;
    cursor: pointer;
}
.theme-select select option { color: #111; background: #fff; }

/* Pages embedded in an iframe inherit the parent's header, but keep a way home */
html.embedded .toolbar { display: none; }  /* the top level page already has the toolbar */
html.embedded .page-header:not(.detail) { display: none; }
html.embedded .page-header.detail .logo-link { display: none; }
html.embedded .page-header.detail .page-header-inner { padding: 12px 28px; }
html.embedded .page-header.detail .page-title { font-size: 22px; }
html.embedded .page-main { padding-top: 14px; }
.page-title .info-badge { margin-left: 10px; vertical-align: middle; background: rgba(255, 255, 255, 0.22); box-shadow: none; border: 1px solid rgba(255, 255, 255, 0.5); }
.page-title .info-badge:hover { background: rgba(255, 255, 255, 0.4); }
.page-title { cursor: help; }

/* ---------- Layout ---------- */
.page-main { max-width: 1500px; margin: 0 auto; padding: 22px 28px 48px 28px; }

/* ---------- Tabs ---------- */
.tab-menu {
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
    padding: 0 8px;
    border-bottom: 1px solid var(--line);
    background: var(--tab-bar);
    border-radius: var(--radius) var(--radius) 0 0;
    border: 1px solid var(--line);
    border-bottom: none;
}
.tab-button {
    appearance: none;
    position: relative;
    margin: 8px 0 0 0;
    padding: 10px 24px 11px 24px;
    border: 1px solid transparent;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    background: transparent;
    color: var(--muted);
    font: inherit;
    font-weight: 600;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: background-color 0.15s, color 0.15s, box-shadow 0.15s;
}
.tab-button:hover { background: var(--tab-hover); color: var(--title); }
.tab-button:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.tab-button.active {
    background: var(--card);
    color: var(--title);
    border-color: var(--line);
    box-shadow: 0 -2px 6px rgba(15, 29, 51, 0.06);
}
.tab-button.active::before {
    content: "";
    position: absolute;
    left: 0; right: 0; top: -1px;
    height: 3px;
    border-radius: 8px 8px 0 0;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
}
.tab-button.active::after {  /* hides the panel border under the active tab */
    content: "";
    position: absolute;
    left: 0; right: 0; bottom: -1px;
    height: 2px;
    background: var(--card);
}

.tab-content {
    display: none;
    background: var(--card);
    border: 1px solid var(--line);
    border-top: none;
    border-radius: 0 0 var(--radius) var(--radius);
    padding: 22px;
    box-shadow: 0 6px 18px var(--shadow);
    animation: fadeIn 0.3s ease;
}
.tab-content.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

/* ---------- Cards ---------- */
.card {
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--card);
    margin-bottom: 22px;
    box-shadow: 0 1px 3px var(--shadow);
    overflow: hidden;
}
.card:last-child { margin-bottom: 0; }
.card-title {
    font-family: var(--title-font);
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0;
    padding: 12px 18px;
    font-size: 16px;
    font-weight: 600;
    color: var(--title);
    background: linear-gradient(180deg, var(--head-a) 0%, var(--head-b) 100%);
    border-bottom: 1px solid var(--line);
    cursor: help;
}
.card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(180deg, var(--head-a) 0%, var(--head-b) 100%);
    border-bottom: 1px solid var(--line);
}
.card-head .card-title { flex: 1; background: none; border: none; }
.card-controls { padding: 0 16px; }
.scale-select { font-size: 13px; font-weight: 600; color: var(--title); }
.scale-select select {
    margin-left: 6px; padding: 4px 8px; font: inherit; font-weight: 400;
    border: 1px solid var(--input-border); border-radius: 5px; background: var(--input-bg); color: var(--ink); cursor: pointer;
}
.paragraph { margin: 4px 2px; font-size: 15px; line-height: 1.6; white-space: pre-line; max-width: 100ch; }

/* Milestone indicators */
.badge { display: inline-block; padding: 2px 10px; border-radius: 11px; font-size: 12px; font-weight: 600; white-space: nowrap; }
.badge-missing { background: var(--bad); color: var(--on-bad); letter-spacing: 0.05em; }
.badge-over { background: var(--bad); color: var(--on-bad); }
.card table.dataframe tbody tr.over-row { background-color: var(--over) !important; box-shadow: inset 4px 0 0 var(--bad); }
.tile-warn { border-color: var(--bad); background: var(--over); }
.tile-warn .tile-value { color: var(--bad); }
.badge-current { background: var(--accent); color: var(--on-accent); box-shadow: 0 1px 3px var(--shadow); }
.badge-passed { background: var(--hover); color: var(--muted); }
.badge-upcoming { background: transparent; color: var(--link); border: 1px solid var(--line); }
.card table.dataframe tbody tr.current-row { background-color: var(--current) !important; box-shadow: inset 4px 0 0 var(--accent); font-weight: 600; }
.pbar {
    position: relative;
    min-width: 110px;
    height: 20px;
    border-radius: 10px;
    background: var(--line);
    overflow: hidden;
}
.pbar::before {
    content: "";
    position: absolute; left: 0; top: 0; bottom: 0;
    width: var(--pct);
    background: linear-gradient(180deg, var(--accent-2), var(--accent));
}
.pbar span { position: relative; display: block; text-align: center; font-size: 12px; font-weight: 600; line-height: 20px; color: var(--ink); text-shadow: 0 0 3px var(--card); }

.tiles { display: flex; flex-wrap: wrap; gap: 12px; }
.tile {
    flex: 1 1 130px;
    padding: 12px 16px;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: linear-gradient(180deg, var(--head-a) 0%, var(--head-b) 100%);
    box-shadow: 0 1px 3px var(--shadow);
}
.tile-main { background: linear-gradient(135deg, var(--band-light), var(--band-mid)); border-color: var(--band-mid); }
.tile-value { font-size: 22px; font-weight: 600; color: var(--title); line-height: 1.2; }
.tile-label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }
.tile-main .tile-value, .tile-main .tile-label { color: var(--on-dark); }
.card-title-bare { justify-content: flex-end; padding: 6px 12px; font-size: 12px; }
.card-body { padding: 14px 16px 16px 16px; }
.chart-wrap { overflow-x: auto; }
.table-wrap { overflow-x: auto; }
.empty { color: var(--muted); font-style: italic; margin: 8px 0; }

.info-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px; height: 18px;
    border-radius: 50%;
    background: var(--accent);
    color: var(--on-accent);
    font: italic 700 12px/1 Georgia, serif;
    cursor: help;
    flex: none;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
}
.info-badge:hover, .info-badge:focus { background: var(--accent-dark); outline: none; }

/* ---------- Tables ---------- */
.card table.dataTable, .card table.dataframe {
    width: 100% !important;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
    font-size: 13px;
    margin: 10px 0;
}
.card table.dataframe thead tr { text-align: left !important; }
.card table.dataframe thead th {
    background: linear-gradient(180deg, var(--band-light), var(--band-mid));
    color: var(--on-dark);
    font-weight: 600;
    text-align: left;
    padding: 10px 28px 10px 12px;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.12);
    white-space: nowrap;
    cursor: pointer;
}
.card table.dataframe thead tr:nth-child(2) th {  /* filter row */
    background: var(--filter-bg);
    padding: 6px 8px;
    cursor: default;
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
}
.card table.dataframe thead tr:nth-child(2) th::before,
.card table.dataframe thead tr:nth-child(2) th::after { display: none !important; }
.card table.dataframe thead input {
    width: 100%;
    min-width: 70px;
    padding: 5px 8px;
    border: 1px solid var(--input-border);
    border-radius: 5px;
    font: inherit;
    font-size: 12px;
    background: var(--input-bg);
    color: var(--ink);
}
.card table.dataframe thead input:focus { outline: 2px solid var(--accent); border-color: var(--accent); }

/* Zebra striping + hover (nth-child so it survives sorting and filtering) */
.card table.dataframe tbody tr { background-color: var(--row-odd); }
.card table.dataframe tbody tr:nth-child(even) { background-color: var(--zebra); }
.card table.dataframe tbody tr:hover { background-color: var(--hover); }
.card table.dataframe tbody td, .card table.dataframe tbody th {
    padding: 8px 12px;
    text-align: left;
    border: none;
    border-bottom: 1px solid var(--row-line);
    background: transparent !important;
    vertical-align: top;
}
.card table.dataframe tbody tr:last-child td { border-bottom: none; }
.card table.dataframe tbody td.sorting_1 { font-weight: 600; }
.card table.kv-table tbody th { font-weight: 600; color: var(--title); width: 220px; }

/* DataTables sort arrows */
table.dataTable thead .sorting:before, table.dataTable thead .sorting_asc:before, table.dataTable thead .sorting_desc:before,
table.dataTable thead .sorting:after,  table.dataTable thead .sorting_asc:after,  table.dataTable thead .sorting_desc:after { color: var(--on-dark); }

/* DataTables controls */
.dataTables_wrapper { color: var(--ink); }
.dataTables_wrapper .dataTables_length select,
.dataTables_wrapper .dataTables_filter input {
    border: 1px solid var(--input-border); border-radius: 5px; padding: 4px 8px; font: inherit; background: var(--input-bg); color: var(--ink);
}
.dataTables_wrapper .dataTables_info { color: var(--muted); font-size: 12px; padding-top: 12px; }
.dataTables_wrapper .dataTables_paginate { padding-top: 8px; }
.dataTables_wrapper .dataTables_paginate .paginate_button.disabled,
.dataTables_wrapper .dataTables_paginate .paginate_button.disabled:hover { color: var(--muted) !important; background: transparent !important; }
.dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter { color: var(--ink); }
.dataTables_wrapper .dataTables_paginate .paginate_button {
    border-radius: 5px; border: 1px solid transparent; padding: 3px 10px; color: var(--ink) !important;
}
.dataTables_wrapper .dataTables_paginate .paginate_button.current,
.dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {
    background: var(--accent) !important; color: var(--on-accent) !important; border-color: var(--accent-dark);
}
.dataTables_wrapper .dataTables_paginate .paginate_button:hover {
    background: var(--hover) !important; color: var(--ink) !important; border-color: var(--line);
}

/* ---------- Embedded pages ---------- */
.full-page-iframe { border: none; width: 100%; height: calc(100vh - 190px); min-height: 500px; display: block; }

/* ---------- Tooltip ---------- */
#tooltip {
    position: fixed;
    z-index: 10000;
    max-width: 360px;
    padding: 10px 13px;
    border-radius: 8px;
    background: var(--tooltip-bg);
    color: var(--tooltip-text);
    font-size: 12.5px;
    line-height: 1.45;
    white-space: pre-line;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.12);
    pointer-events: none;
    opacity: 0;
    transform: translateY(4px);
    transition: opacity 0.12s, transform 0.12s;
}
#tooltip.visible { opacity: 1; transform: none; }
[data-tip] { cursor: help; }
th[data-tip], input[data-tip], a[data-tip] { cursor: pointer; }
input[data-tip] { cursor: text; }
"""

JS = r"""
(function () {
    // Mark pages that are shown inside an iframe so the banner can be hidden
    try { if (window.self !== window.top) document.documentElement.classList.add('embedded'); }
    catch (e) { document.documentElement.classList.add('embedded'); }
})();

var COLUMN_HELP = __COLUMN_HELP__;
var FILTER_TIP = "Filter this column. Plain text matches anywhere in the cell (case-insensitive).\n" +
                 "Operators: > >= < <= compare numbers, = and != match exactly, ^= starts with, $= ends with, ~= regular expression.";

$(document).ready(function() {

    function toPlainText(htmlOrText) {
        return $('<div>').html(htmlOrText).text().trim();
    }

    function tryNumber(s) {
        if (s === null || s === undefined) return NaN;
        s = String(s).trim().replace(/^(-?[\d.]+)\s*(my|mm|mw|md)$/, '$1');
        s = s.replace(/[, £$%]/g, '').trim();
        if (s === '') return NaN;
        var n = Number(s);
        return isNaN(n) ? NaN : n;
    }

    $('table.dataframe').each(function() {
        var $table = $(this);
        var rows = $table.find('tbody tr').length;

        // Column guidance on the heading cells
        $table.find('thead tr:eq(0) th').each(function() {
            var name = $(this).text().trim();
            var tip = COLUMN_HELP[name] || '';
            var sortTip = 'Click to sort by this column.';
            $(this).attr('data-tip', tip ? name + '\n' + tip + '\n\n' + sortTip : sortTip);
        });

        // Clone header row for filters
        $table.find('thead tr').clone(true).appendTo($table.find('thead'));
        $table.find('thead tr:eq(1) th').each(function() {
            var title = $(this).text().trim();
            $(this).removeAttr('data-tip').html('<input type="text" class="col-filter" placeholder="Filter ' + title + '" data-tip="' +
                                                FILTER_TIP.replace(/"/g, '&quot;') + '" />');
        });

        // Initialize DataTable
        $table.DataTable({
            order: [],
            orderCellsTop: true,
            fixedHeader: false,
            pageLength: 25,
            createdRow: function(row) {
                if ($(row).find('.badge-current').length) $(row).addClass('current-row');
                if ($(row).find('.badge-over').length) $(row).addClass('over-row');
            },
            paging: rows > 10,
            lengthChange: rows > 10,
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
            language: { search: "Search all columns:", zeroRecords: "No rows match the current filters" }
        });
    });

    // Pre-fill column filters from the page address, e.g. tasks/index.html#project=Project%20Alpha
    var hash = decodeURIComponent(window.location.hash.slice(1));
    if (hash) {
        hash.split('&').forEach(function(pair) {
            var i = pair.indexOf('=');
            if (i < 1) return;
            var key = pair.slice(0, i).trim().toLowerCase(), val = pair.slice(i + 1);
            $('table.dataframe').each(function() {
                var $t = $(this);
                $t.find('thead tr:eq(0) th').each(function(c) {
                    if ($(this).text().trim().toLowerCase() === key) {
                        $t.find('thead tr:eq(1) th').eq(c).find('input').val(val);
                    }
                });
            });
        });
    }

    // Custom filter logic
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        var valid = true;
        var $table = $(settings.nTable);

        $table.find('thead tr:eq(1) th input').each(function(i) {
            var val = $(this).val();
            if (!val) return;
            val = val.trim();

            var cell = toPlainText(data[i]);

            var m = val.match(/^([<>]=?|!=|=|\^=|\$=|~=)\s*(.*)$/);
            if (m) {
                var op = m[1], rhs = m[2].trim();

                if (op === '=')  { valid = valid && (cell === rhs); return; }
                if (op === '!=') { valid = valid && (cell !== rhs); return; }
                if (op === '^=') { valid = valid && cell.startsWith(rhs); return; }
                if (op === '$=') { valid = valid && cell.endsWith(rhs); return; }
                if (op === '~=') {
                    try { valid = valid && (new RegExp(rhs)).test(cell); }
                    catch(e) { valid = false; }
                    return;
                }

                var lhsNum = tryNumber(cell);
                var rhsNum = tryNumber(rhs);
                if (isNaN(lhsNum) || isNaN(rhsNum)) {
                    valid = false;
                    return;
                }
                if (op === '>')  valid = valid && (lhsNum > rhsNum);
                if (op === '>=') valid = valid && (lhsNum >= rhsNum);
                if (op === '<')  valid = valid && (lhsNum < rhsNum);
                if (op === '<=') valid = valid && (lhsNum <= rhsNum);
                return;
            }

            if (cell.toLowerCase().indexOf(val.toLowerCase()) === -1) valid = false;
        });

        return valid;
    });

    // Redraw when filters change
    $(document).on('keyup change input search', 'input.col-filter', function() {
        $(this).closest('table').DataTable().draw();
    });

    // Apply any filters taken from the page address
    if (hash) $('table.dataframe').each(function() { $(this).DataTable().draw(); });

    // ---------- Tooltips ----------
    var tip = document.getElementById('tooltip');

    function place(x, y) {
        var pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
        var left = Math.min(x + pad, window.innerWidth - w - 8);
        var top = y + pad + h > window.innerHeight ? y - h - pad : y + pad;
        tip.style.left = Math.max(8, left) + 'px';
        tip.style.top = Math.max(8, top) + 'px';
    }

    function show(el, x, y) {
        var text = el.getAttribute('data-tip');
        if (!text) return;
        tip.textContent = text;
        place(x, y);
        tip.classList.add('visible');
    }

    $(document).on('mouseover', '[data-tip]', function(e) { show(this, e.clientX, e.clientY); });
    $(document).on('mousemove', '[data-tip]', function(e) { place(e.clientX, e.clientY); });
    $(document).on('mouseout', '[data-tip]', function() { tip.classList.remove('visible'); });
    $(document).on('focusin', '[data-tip]', function() {
        var r = this.getBoundingClientRect(); show(this, r.left, r.bottom);
    });
    $(document).on('focusout', '[data-tip]', function() { tip.classList.remove('visible'); });

    // ---------- Themes ----------
    var embedded = document.documentElement.classList.contains('embedded');
    var select = document.getElementById('theme-select');

    // How to restyle the charts for each theme: plotly layout properties, and how the bars are coloured
    var CHART = __CHART_THEMES__;
    var DEFAULT_THEME = __DEFAULT_THEME__;

    // Indices of the traces that are real bars (not the shading overlays)
    function barTraces(el) {
        var idx = [];
        (el.data || []).forEach(function(t, i) {
            if (t.type === 'bar' && t.showlegend !== false && t.name !== '') idx.push(i);
        });
        return idx;
    }

    // Indices of the traces drawn in the text colour of the theme (see INK in _charts.py)
    function inkTraces(el) {
        var idx = [];
        (el.data || []).forEach(function(t, i) { if (t.meta === 'ink') idx.push(i); });
        return idx;
    }

    function restyleCharts(theme) {
        if (!window.Plotly) return;
        document.querySelectorAll('.js-plotly-plot').forEach(function(el) {
            var bars = barTraces(el);

            // Remember the original colours the first time we see the chart
            if (!el.__orig) el.__orig = bars.map(function(i) { return el.data[i].marker.color; });

            var t = CHART[theme] || CHART[DEFAULT_THEME];
            Plotly.relayout(el, t.layout);

            var ink = inkTraces(el), color = t.layout['font.color'];
            if (ink.length && color) {
                Plotly.restyle(el, {'line.color': color, 'marker.color': color, 'marker.line.color': color,
                                    'textfont.color': color}, ink);
            }

            if (bars.length) {
                var colors = el.__orig;
                if (t.bars.mode === 'ramp') {
                    // Spread bars over a ramp of lightness, stepping by the golden ratio so neighbours differ
                    var lo = t.bars.lightness[0], hi = t.bars.lightness[1];
                    colors = bars.map(function(b, k) {
                        var l = lo + (hi - lo) * ((k * 0.618034) % 1);
                        return 'hsl(' + t.bars.hue + ',' + t.bars.saturation + '%,' + l.toFixed(0) + '%)';
                    });
                } else if (t.bars.mode === 'palette') {
                    colors = bars.map(function(b, k) { return t.bars.palette[k % t.bars.palette.length]; });
                }
                Plotly.restyle(el, {'marker.color': colors, 'hoverlabel.bordercolor': colors}, bars);
            }
        });
    }

    var current = document.documentElement.getAttribute('data-theme') || DEFAULT_THEME;

    function applyTheme(theme, save) {
        current = theme;
        document.documentElement.setAttribute('data-theme', theme);
        if (select) select.value = theme;
        restyleCharts(theme);

        if (save) {
            try { localStorage.setItem('apheleia-theme', theme); } catch (e) {}
            window.name = 'apheleia-theme=' + theme;   // survives navigation when storage is blocked
        }

        // Tell any embedded pages
        document.querySelectorAll('iframe').forEach(function(f) {
            try { f.contentWindow.postMessage({type: 'apheleia-theme', theme: theme}, '*'); } catch (e) {}
        });
    }

    if (select) select.addEventListener('change', function() { applyTheme(this.value, true); });

    window.addEventListener('message', function(e) {
        var m = e.data;
        if (!m || typeof m !== 'object') return;
        if (m.type === 'apheleia-theme') applyTheme(m.theme, false);
        if (m.type === 'apheleia-theme-request' && e.source) {
            e.source.postMessage({type: 'apheleia-theme', theme: current}, '*');
        }
    });

    // Embedded pages follow the theme chosen on the top level page
    if (embedded && window.parent !== window) {
        window.parent.postMessage({type: 'apheleia-theme-request'}, '*');
    }


    // Charts are drawn by scripts further down the page, so restyle once everything has loaded
    // Only if the theme changes how the charts look, and the load event may already have happened by now
    if (CHART[current].restyle) {
        if (document.readyState === 'complete') restyleCharts(current);
        else window.addEventListener('load', function() { restyleCharts(current); });
    }
    if (select) select.value = current;

    // Ensure the first tab is resized correctly once everything is loaded
    window.dispatchEvent(new Event('resize'));
});

var EFFORT_UNITS = {my : 12, mm : 1, mw : 0.25, md : 0.05};   // man-months in one of each unit

// Effort cells: <span class="effort" data-mm="<man-months>">. Sort them by value. Empty cells (no estimate) sort first
$.fn.dataTable.ext.type.detect.unshift(function(d) {
    return (d === '' || (typeof d === 'string' && /^<span class="effort"[^>]*>[^<]*<\/span>$/.test(d))) ? 'effort' : null;
});
$.fn.dataTable.ext.type.order['effort-pre'] = function(d) {
    var m = /data-mm="([^"]*)"/.exec(d);
    return m ? parseFloat(m[1]) : -Infinity;
};

function formatEffort(mm, unit) {
    var v = mm / EFFORT_UNITS[unit];
    return String(parseFloat(v.toFixed(2))) + ' ' + unit;
}

function setEffortUnit(unit, remember) {
    document.querySelectorAll('span.effort').forEach(function(e) {
        e.textContent = formatEffort(parseFloat(e.dataset.mm), unit);
    });
    document.querySelectorAll('select.effort-unit').forEach(function(sel) { sel.value = unit; });
    // Tables cache their cells, so read them again to sort and filter on the new unit
    $('table.dataframe').each(function() {
        if ($.fn.dataTable.isDataTable(this) && $(this).find('span.effort').length) {
            $(this).DataTable().rows().invalidate('dom').draw(false);
        }
    });
    if (remember) { try { localStorage.setItem('apheleia-effort-unit', unit); } catch (e) {} }
}

$(document).ready(function() {
    var unit = 'mm';
    try { unit = localStorage.getItem('apheleia-effort-unit') || 'mm'; } catch (e) {}
    if (!EFFORT_UNITS[unit]) unit = 'mm';
    if (unit !== 'mm') setEffortUnit(unit, false);
});

function setTicks(sel) {
    var o = sel.options[sel.selectedIndex];
    sel.closest('.card').querySelectorAll('.js-plotly-plot').forEach(function(p) {
        Plotly.relayout(p, {'xaxis.dtick': o.value, 'xaxis.tickformat': o.dataset.fmt});
    });
}

function openTab(event, tabId) {
    document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
    document.querySelectorAll('.tab-button').forEach(function(b) {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
    });

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
    event.currentTarget.setAttribute('aria-selected', 'true');

    // Plotly (and DataTables) need a resize event to lay out charts that were hidden
    window.dispatchEvent(new Event('resize'));
}
"""


class HTMLTab:

    def __init__(self, title : str, parent) -> None:
        """
        Constructor

        :param title: str
        :type title: str
        :return: None
        """

        self.title = title
        """ Title of the section """

        self.id = value_to_filename(title)
        """ Id of the section """

        self.parent = parent
        """ Parent container """

        self.sections = []
        """ User added sections """

    def __str__(self) -> str:
        """
        String representation of the class

        :return: str
        """

        return "".join(self.sections)

    def _card(self, title : str, help : str, extra_tip : str, body : str, kind : str, controls : str="") -> str:
        """
        Wrap content in a titled card with a hover guidance badge

        :param title: Title of the card (may be empty)
        :param help: Guidance text. Falls back to a default for the title
        :param extra_tip: Interaction guidance appended to the help
        :param body: Html body of the card
        :param kind: css class (table / chart)
        :param controls: Optional html (e.g. a select box) shown at the right of the card header
        """

        text = help or SECTION_HELP.get(title.strip().lower(), "")
        tip = f"{text}\n\n{extra_tip}" if text else extra_tip

        heading = ""
        if title:
            heading = f'<h2 class="card-title"{_tip(tip)}>{_html.escape(title)}{_info_badge(tip)}</h2>'
        else:
            heading = f'<div class="card-title card-title-bare">{_info_badge(tip)}</div>'

        if controls:
            heading = f'<div class="card-head">{heading}<div class="card-controls">{controls}</div></div>'

        return f'\n<section class="card {kind}-card">{heading}<div class="card-body">{body}</div></section>\n'

    def add_table(self, title : str, df : pd.DataFrame, transpose=False, help : str="", units : bool=False) -> None:
        """
        Add a table to the html file

        :param title: Title of the table
        :param df: Data
        :param transpose: Show as a field / value table (one row per column of df)
        :param help: Hover guidance explaining what the table means
        :param units: Add a select box for the unit of effort. Effort in the table is written as html spans from _workpackages.format_months
        """

        if transpose:
            table = self.format_df_for_html(df.T).to_html(header=False, escape=False, classes="dataframe kv-table")

            # Fix for DataTables / Pandas mismatch
            table = table.replace('<tbody>', '<thead><tr><th>Field</th><th>Value</th></tr></thead><tbody>', 1)
        else:
            table = self.format_df_for_html(df).to_html(index=False, escape=False)

        controls = ""
        if units:
            controls = ('<label class="scale-select">Units '
                        '<select class="effort-unit" onchange="setEffortUnit(this.value, true)" '
                        'data-tip="Show effort in man-years (my), man-months (mm), man-weeks (mw) or man-days (md). '
                        'A man-month is 4 man-weeks or 20 man-days, and a man-year is 12 man-months.">'
                        '<option value="my">my</option><option value="mm" selected>mm</option>'
                        '<option value="mw">mw</option><option value="md">md</option></select></label>')

        self.sections.append(self._card(title, help, TABLE_TIP, f'<div class="table-wrap">{table}</div>', "table", controls=controls))

    def _click_script(self, chart) -> (str | None):
        """
        Javascript making the bars of a chart link to their container pages

        Charts opt in by setting layout.meta["link_key"] to a container type. The y value of
        the bar is looked up in that container type and the bar then links to its html page.

        The handlers are on the chart's html element, not Plotly's own events, because Plotly throws its events
        away whenever it redraws a chart, e.g. when it is resized or a theme is applied. A click is a click on a
        bar being hovered over, that was not a drag (which zooms or pans the chart).

        :param chart: Plotly figure
        :return: Javascript (or None if the chart has no links)
        """

        meta = chart.layout.meta
        if not isinstance(meta, dict) or "link_key" not in meta:
            return None

        from ._containers import containers

        links = {}
        for name, container in containers.get(meta["link_key"], {}).items():
            relative = os.path.relpath(container.html.path, self.parent.path.parent)
            links[name] = relative.replace(os.sep, "/")

        return """
var gd = document.getElementById('{plot_id}');
var links = """ + json.dumps(links) + """;
var byTrace = """ + json.dumps(meta.get("link_by") == "trace") + """;
var fixed = """ + json.dumps(meta.get("link_to")) + """;
function target() {
    var p = (gd._hoverdata || [])[0];
    if (!p) return null;
    return links[fixed !== null ? fixed : (byTrace ? p.data.name : p.y)] || null;
}
var down = null;
gd.addEventListener('mousedown', function(e) { down = [e.clientX, e.clientY]; });
gd.addEventListener('mousemove', function() { gd.style.cursor = target() ? 'pointer' : ''; });
gd.addEventListener('click', function(e) {
    var dragged = !down || Math.abs(e.clientX - down[0]) > 4 || Math.abs(e.clientY - down[1]) > 4;
    var url = target();
    if (url && !dragged) window.open(url, '_top');
});
"""

    def add_chart(self, title : str, chart, help : str="") -> None:
        """
        Add a chart to the html file

        :param title: Title of the chart
        :param chart: Plotly figure
        :param help: Hover guidance explaining what the chart means
        """

        # A dictionary of scale to chart gets a select box to choose between them
        if isinstance(chart, dict):
            self.add_scaled_chart(title, chart, help=help)
            return

        controls = ""
        if chart is not None:
            body = f'<div class="chart-wrap">{chart.to_html(full_html=False, include_plotlyjs="cdn", post_script=self._click_script(chart), config={"responsive": True})}</div>'

            # Charts with a date axis can change how often the axis is labelled
            meta = chart.layout.meta
            if isinstance(meta, dict) and meta.get("scale_ticks"):
                controls = self._tick_select(meta.get("scale_default", "Quarterly"))
        else:
            body = '<p class="empty">No data available.</p>'

        self.sections.append(self._card(title, help, CHART_TIP, body, "chart", controls=controls))

    def _tick_select(self, default : str) -> str:
        """
        Select box changing the spacing of the date labels of the charts in the same card

        :param default: Scale selected initially
        :return: Html
        """

        ticks = {"Monthly" : ("M1", "%b<br>%Y"), "Quarterly" : ("M3", "%b<br>%Y"), "Yearly" : ("M12", "%Y")}
        options = ""
        for name, (dtick, fmt) in ticks.items():
            selected = " selected" if name == default else ""
            options += f'<option value="{dtick}" data-fmt="{_html.escape(fmt)}"{selected}>{name}</option>'

        return ('<label class="scale-select">Scale '
                '<select onchange="setTicks(this)" data-tip="Change how often the date axis is labelled.">'
                f'{options}</select></label>')

    def add_paragraph(self, title : str, text : str, help : str="") -> None:
        """
        Add a paragraph of text

        :param title: Title of the card
        :param text: Text. Line breaks are kept
        :param help: Hover guidance explaining what the text is
        """

        self.sections.append(self._card(title, help, "", f'<p class="paragraph">{_html.escape(str(text))}</p>', "text"))

    def add_summary(self, title : str, items : list, help : str="") -> None:
        """
        Add a row of summary tiles

        :param title: Title of the summary
        :param items: List of (label, value) or (label, value, warn) tuples. Tiles with warn set are highlighted
        :param help: Hover guidance explaining what the summary means
        """

        tiles = "".join(
            f'<div class="tile{" tile-main" if i == 0 else ""}{" tile-warn" if warn else ""}">'
            f'<div class="tile-value">{_html.escape(str(v))}</div><div class="tile-label">{_html.escape(str(k))}</div></div>'
            for i, (k, v, *flag) in enumerate(items) for warn in [bool(flag and flag[0])]
        )
        self.sections.append(self._card(title, help, "", f'<div class="tiles">{tiles}</div>', "summary"))

    def add_scaled_chart(self, title : str, charts : dict, label : str="Scale", help : str="") -> None:
        """
        Add a chart with a select box that switches between several versions of it

        :param title: Title of the chart
        :param charts: Dictionary of select box label to Plotly figure. The first is shown initially
        :param label: Label of the select box
        :param help: Hover guidance explaining what the chart means
        """

        options = ""
        panes = ""
        first = True
        for name, chart in charts.items():
            n = _html.escape(name, quote=True)
            options += f'<option value="{n}">{n}</option>'
            # Only the first figure needs to load plotly itself
            plotly_js = "cdn" if first else False
            figure = chart.to_html(full_html=False, include_plotlyjs=plotly_js, post_script=self._click_script(chart), config={"responsive": True})
            panes += f'<div class="scale-pane" data-scale="{n}" style="display:{"block" if first else "none"}">{figure}</div>'
            first = False

        select = (f'<label class="scale-select">{_html.escape(label)} '
                  f'<select data-tip="Change the time period each bar covers." '
                  f"onchange=\"var c=this.closest('.card');"
                  f"c.querySelectorAll('.scale-pane').forEach(function(p){{p.style.display=(p.dataset.scale===this.value)?'block':'none';}},this);"
                  f"window.dispatchEvent(new Event('resize'));\">{options}</select></label>")

        body = f'<div class="chart-wrap">{panes}</div>'
        self.sections.append(self._card(title, help, CHART_TIP, body, "chart", controls=select))

    def embed_url(self, url):
        """
        Embed a url in the html file

        param: url
        type: str
        """
        s = f"""
<iframe src="{_html.escape(url, quote=True)}" class="full-page-iframe">
    <p>Your browser does not support iframes.</p>
</iframe>
"""
        self.sections.append(s)

    def format_df_for_html(self, df : pd.DataFrame) -> pd.DataFrame:
        """
        Format a dataframe for html

        :param df: pd.DataFrame
        :return: pd.DataFrame
        """
        def make_link(col, val):

            if not isinstance(val, str):
                return val

            # Hard coded paths
            s = val.strip()
            if s.startswith("http"):
                return f'<a href="{s}" target="_blank" rel="noopener">{s}</a>'

            # Container Lookup
            from ._containers import containers
            if col in containers.keys():
                def link(name):
                    full_path = containers[col][name].html.path
                    relative_path = full_path.relative_to(self.parent.path.parent, walk_up=True)
                    return f'<a href="{relative_path}">{name}</a>'

                if val in containers[col].keys():
                    return link(val)

                # Several names, e.g. the resources of a shared task
                names = val.split(", ")
                if len(names) > 1 and all(n in containers[col] for n in names):
                    return ", ".join(link(n) for n in names)

            return val

        def format_dates(val):
            if isinstance(val, pd.Timestamp):
                return val.strftime('%Y-%m-%d')

            return val

        df = df.copy()

        for col in df.columns:

            # Date columns: format here so that missing dates show as empty, not NaT
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d').fillna("")

            # Replace None Strings
            df[col] = df[col].fillna("")

            # Format dates to YYYY-MM-DD format
            df[col] = df[col].apply(format_dates)

            # Create links
            df[col] = df[col].apply(lambda x, col=col: make_link(col, x))

        return df

class HTML:

    def __init__(self, parent, path : Path) -> None:
        """
        Constructor
        """

        self.parent = parent
        """ Parent container """

        self.path = path
        """ Path to html file """

        self.tabs = []
        """ User added tabs """

        self.format = _format.active()
        """ Text, logo and themes of the report """

    def __str__(self) -> str:
        """
        String representation of the class

        :return: str
        """

        s = "<!DOCTYPE html>\n<html lang=\"en\">\n" + self.head() + self.body() + "\n</html>\n"
        return s

    def titles(self) -> tuple[str, str]:
        """
        Kicker and title for the page banner

        :return: (kicker, title)
        """

        if self.parent is None:
            return self.format.kicker, self.format.title

        kind = str(getattr(self.parent, "container_type", "")).title()
        name = str(self.parent.name)
        if name == "index":
            return "Overview", kind or "Overview"
        return kind, name

    def is_detail(self) -> bool:
        """ True for the page of a single project / workpackage / resource etc. """

        return self.parent is not None and str(self.parent.name) != "index"

    def describe(self) -> str:
        """
        Text explaining what the page represents, shown when hovering over the page title

        :return: str
        """

        if self.parent is None:
            return ("Top level index of the project management report.\n"
                    "Use the tabs to browse projects, resources and milestones. "
                    "Click any name in a table or bar in a chart to open its page.")

        kind = str(getattr(self.parent, "container_type", ""))
        name = str(self.parent.name)

        if not self.is_detail():
            return INDEX_HELP.get(kind, f"Overview of all {kind}.")

        lines = [f"{kind.title()}: {name}"]

        df = getattr(self.parent, "imported_df", None)
        if df is not None and len(df) > 0:
            if "description" in df.columns:
                desc = df["description"].dropna()
                desc = desc[desc.astype(str).str.strip() != ""]
                if len(desc) > 0:
                    lines.append(str(desc.iloc[0]))

            # Facts that help describe the item
            def first(col):
                if col in df.columns:
                    v = df[col].dropna()
                    v = v[v.astype(str).str.strip() != ""]
                    if len(v) > 0:
                        v = v.iloc[0]
                        return v.strftime("%Y-%m-%d") if isinstance(v, pd.Timestamp) else str(v)
                return None

            facts = []
            if kind == "resource":
                start = pd.to_datetime(df["start"]) if "start" in df.columns else pd.Series(dtype="datetime64[ns]")
                end = pd.to_datetime(df["end"]) if "end" in df.columns else pd.Series(dtype="datetime64[ns]")
                facts += [("User name", first("uname")),
                          ("Available from", f"{start.min():%Y-%m-%d}" if len(start) and start.notna().all() else None),
                          ("Available to", f"{end.max():%Y-%m-%d}" if len(end) and end.notna().all() else "open ended")]
                if len(df) > 1:
                    facts.append(("Availability periods", str(len(df))))
            elif kind == "project":
                facts += [("Start", first("start")), ("End", first("end") or "open ended")]
            elif kind in ("workpackage", "task"):
                facts += [("Project", first("project")), ("Workpackage", first("workpackage") if kind == "task" else None),
                          ("Resource", first("resource") if kind == "task" else None)]
            if kind == "task":
                facts += [("Start", first("start") or "not given, defaults to the previous milestone"),
                          ("Estimate", first("estimate") or "MISSING - no estimate has been provided")]
            for k, v in facts:
                if v:
                    lines.append(f"{k}: {v}")

        lines.append("")
        lines.append(DETAIL_HELP.get(kind, ""))
        return "\n".join(lines).strip()

    def home_link(self, css : str = "home-link") -> str:
        """
        Link back to the top level index.html

        :param css: css class of the link
        :return: str
        """

        if self.parent is None:
            href = "index.html"
        else:
            root = self.parent.path.parent / "index.html"
            href = os.path.relpath(root, self.path.parent).replace(os.sep, "/")

        return (f'<a class="{css}" href="{_html.escape(href, quote=True)}" target="_top" '
                f'data-tip="Return to the top level index page.">&#8592; Home</a>')

    def logo(self) -> str:
        """
        Code for logo

        :return: str
        """

        fmt = self.format
        if not fmt.logo:
            return ""

        style = f' style="--logo-height: {fmt.logo_height}px"'
        tip = _tip(fmt.logo_tooltip) if fmt.logo_tooltip else ""
        if fmt.logo_link:
            return f"""
<a class="logo-link" href="{_html.escape(fmt.logo_link, quote=True)}" target="_blank" rel="noopener"{style}{tip}>
{fmt.logo}
</a>
"""
        return f"""
<div class="logo-link"{style}{tip}>
{fmt.logo}
</div>
"""

    def early_js(self) -> str:
        """ Script run before the page is drawn, to apply the saved theme """

        names = json.dumps([t.name for t in self.format.themes])
        return EARLY_JS.replace("__THEME_NAMES__", names).replace("__DEFAULT_THEME__", json.dumps(self.format.default_theme))

    def js(self) -> str:
        """ Script of the page """

        return (JS.replace("__COLUMN_HELP__", json.dumps(COLUMN_HELP))
                  .replace("__CHART_THEMES__", json.dumps(_format.chart_themes(self.format)))
                  .replace("__DEFAULT_THEME__", json.dumps(self.format.default_theme)))

    def head(self) -> str:
        """
        Code for html header

        :return: str
        """

        _, title = self.titles()

        s = f"""
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{_html.escape(title)}</title>
    <link rel="stylesheet"
          href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script>{self.early_js()}</script>
    <style>{CSS.replace("__THEMES_CSS__", _format.theme_css(self.format))}{self.format.css}</style>
    <script>{self.js()}</script>
</head>
"""
        return s

    def body(self) -> str:
        """
        Code for html body

        :return: str
        """

        kicker, title = self.titles()
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        tip = self.describe()
        detail = " detail" if self.is_detail() else ""
        options = "\n".join(f'                <option value="{_html.escape(t.name, quote=True)}">{_html.escape(t.label)}</option>' for t in self.format.themes)
        chooser = f"""
        <label class="theme-select">{_html.escape(self.format.theme_label)}
            <select id="theme-select" data-tip="Change the colour theme of the report. The choice is remembered for all pages.">
{options}
            </select>
        </label>""" if len(self.format.themes) > 1 else ""
        toolbar = f"""
<nav class="toolbar" aria-label="Page tools">
    <div class="toolbar-inner">
        {self.home_link()}{chooser}
    </div>
</nav>
"""

        # Banner
        s = f"""
<body>
{toolbar}
<header class="page-header{detail}">
    <div class="page-header-inner">
        <div>
            <div class="page-kicker">{_html.escape(kicker)}</div>
            <h1 class="page-title"{_tip(tip)}>{_html.escape(title)}{_info_badge(tip)}</h1>
            <div class="page-meta">{_html.escape(self.format.generated.replace("{stamp}", stamp).replace("{today}", today_text()))}</div>
        </div>
        {self.logo()}
    </div>
</header>
<main class="page-main">
"""
        # Tab menu
        s += """
    <div class="tabs">
        <div class="tab-menu" role="tablist">
"""
        active = " active"
        selected = "true"
        for t in self.tabs:
            s += f"""
            <button class="tab-button{active}" role="tab" aria-selected="{selected}" aria-controls="{t.id}" onclick="openTab(event, '{t.id}')">{_html.escape(t.title)}</button>
"""
            active = ""
            selected = "false"
        s += """
        </div>
"""

        # Tab content
        active = " active"
        for t in self.tabs:
            s += f"""
        <div id="{t.id}" class="tab-content{active}" role="tabpanel">
        {t}
        </div>
"""
            active = ""

        # Close
        s += """
    </div>
</main>
<div id="tooltip" role="tooltip"></div>
</body>
"""
        return s

    def add_tab(self, title : str) -> HTMLTab:
        """
        Add a tab to the html file

        :param title: str
        :type title: str
        :return: HTMTab
        """

        tab = HTMLTab(title, self)
        self.tabs.append(tab)

        return tab

    def export(self) -> None:
        """
        Export the html file

        :param path: Path
        :type path: Path
        :return: None
        """

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(str(self))

__all__ = [
    "HTML"
]
