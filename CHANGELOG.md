# Changelog

## [Unreleased]

### Added
 - examples/milestones: `windows`, and `errors` with one directory for each way a milestone can be invalid. An error case passes only if the report exits with a non-zero status and the expected `ERROR :` message; every other example fails unless the report exits with status 0.
 - examples/Makefile: `make report` prints `<example> : PASSED` or `FAILED` as each example finishes, then the number passed and failed, and supports `-j`. `make clean` prints a one line summary.
 - Milestones: a project can give a milestone a `start` and an `end` date instead of a single `date`. These milestones can overlap, and are drawn on the project timeline as a window: a dotted vertical line at each end joined by a horizontal line. Single date milestones are unchanged. In project tables the dates are combined, e.g. `2026-03-01 to 2026-04-30`; the table of projects using a milestone has separate start and end columns, with the start blank for a single date. A window milestone is due on its end date. A milestone with only one of `start` and `end`, a mixture of `date` and `start`/`end`, or an end before its start is reported as an error. The `milestones/windows` example shows both kinds.
 - Milestones: dates can be relative to another milestone of the same project, e.g. `end: "M1.start + 6 months"`, `start: "M1.end - 10 days"` or `end: "start + 7 weeks"`, in days, weeks, months or years. Milestones can refer to each other in any order; unknown milestones and loops are reported as errors.

## [v0.2.0] - 2026-11-07

### Added
 - Workpackages: optional `milestone`. The workpackage must end by the milestone date; starting early is fine. Workpackages that end after it, or whose milestone has no date in the project, are marked `OUTSIDE MILESTONE` in the workpackage tables and listed on the project summary. The milestone is marked with a diamond on the workpackage's bar in the workpackage timelines, and on the bars of its tasks in the task timelines. The `simple` example shows one workpackage within and one outside its milestone.

## [v0.1.0] - 2026-11-07

First release.

### Added
 - Input files: projects, milestones, resources, workpackages and tasks are described in YAML files, each with a `type` (`milestones_definitions`, `resources_definitions`, `projects_definitions`, `workpackages_definitions` or `tasks_definitions`) and a list of `data`. The input directory is searched recursively and all definitions of the same type are combined, so a plan can be one file per type or split by owner. Files with no `type` are ignored. Dates are written as `YYYY-MM-DD`, or `YYYY-MM` for the first of the month; `None`, `null`, `nan` and empty strings are treated as no date, and milestone names of the form `M<number>` are never mistaken for dates. Definitions with no name, duplicate names, unexpected (usually misspelt) fields and files that are not valid YAML are reported as a single `ERROR :` line naming the problem, with a non-zero exit status. Files with an unrecognised `type` are skipped with a warning. Any of the five types can be left out, so a plan can be built up a file at a time.
 - Milestones: named checkpoints defined once and given a date by each project that uses them, so projects can be compared like for like.
 - Resources: people and the period they are available. A resource with no end date is assumed available to the end of the charts.
 - Projects: start and end dates, description and a dated list of milestones, all optional beyond the project name.
 - Workpackages: areas of work within a project and the resources allocated to them, as a fraction of full time over whole months. Effort is reported in person-months, and a workpackage's start and end are taken from its allocations.
 - Tasks: individual pieces of work owned by a single resource, with a history of status updates recording effort spent and remaining in days. An optional `start` defaults to the project's previous milestone, and an optional `estimate` records the original effort in days; tasks whose spent plus remaining effort has grown past their estimate are listed on the project page, and in the Progress by Task chart each bar is split at the estimate, blue within it and red past it, and tasks with no estimate are flagged as missing. Status, percentage complete and a forecast end date are derived from the latest update; the forecast is the remaining effort in working days from the latest update, or from today if an unfinished task's latest update is in the past.
 - `apheleia_project_report`: generates the report from `--input` (default `.`) into `--html` (default `./html`). A top level index has tabs for projects, resources and milestones, and every project, workpackage, resource, task and milestone has an overview page and a page of its own.
 - Project summary: the status of the project's tasks grouped by the milestone they are needed for, and the tasks past their estimate.
 - Report: interactive [plotly](https://plotly.com/python/) charts - project, workpackage and task timelines with milestones and today marked, effort allocated by workpackage, project and resource, resource availability and the number of resources available over time, and task progress. Charts with a time axis can be viewed at monthly, quarterly or yearly scale. Every name in a table and every bar or segment in a chart links to the page for that item, and the same resource has the same colour on every chart. Charts and tables carry a help badge describing what they show.
 - examples/: `simple`, a minimal semiconductor project; `construction_single`, a multi-year construction project with one file per type; and `construction_multi`, the same project split into shared definitions and a tasks file per resource. `make report` and `make clean` in `examples/` build or remove every report, or in an example's own directory just that one.
 - doc/: Sphinx documentation covering installation, the input files, the report and the examples, illustrated with screenshots of the example reports, with an API reference generated by `doc/gen_all_rst.py`. Built with `make html` in `doc/`, and configured for [Read the Docs](https://readthedocs.org/) by `.readthedocs.yaml`. The documented version is read from `pyproject.toml`.
 - `setup.sh`: creates a virtual environment and installs the development build in editable mode, warning if Graphviz is not on PATH.
 - `__version__` is exported from the package, so `apheleia_project_management.__version__` works.
