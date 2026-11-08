.. _report:

Generating Reports
==================

Overview
--------

Apheleia Project Management provides a simple script to generate the report in HTML format. The script is \
exported as a project script and added to your path automatically when the package is installed. \
To generate a report, run the script with the following command:

.. code-block:: shell

    $ apheleia_project_report --input <input directory> --html <output directory> [--today YYYY-MM-DD|None]

To check the input without generating a report, add ``--check`` (see `Checking the input`_):

.. code-block:: shell

    $ apheleia_project_report --check --input <input directory>

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Option
     - Default
     - Description
   * - ``--input``
     - ``.``
     - Directory searched recursively for :doc:`input files <../inputs/inputs>`
   * - ``--html``
     - ``./html``
     - Directory the report is written to. It is created if it does not exist
   * - ``--check``
     - off
     - Only check the input: report any problems and exit, without writing a report. ``--html`` is not needed. \
       See `Checking the input`_
   * - ``--today``
     - the day it is run
     - The report date: the day the report is made for, as ``YYYY-MM-DD``, or ``None`` for a report with no date. \
       See `Report date`_

Open ``index.html`` in the output directory in a browser to view the report.

Report date
-----------

Some of the report depends on what day it is: today is marked on the charts, unfinished tasks are forecast from \
today if their latest status update is older, tasks are ``STALE`` when they have not been updated for a while, \
the current milestone is the next one due, and each resource's availability is shown for today. By default \
today is the day the report is run, so the same plan gives a different report on a different day.

``--today`` fixes the date, so the report is the same whatever day it is made, e.g. ``--today 2026-11-09``. \
Every example sets it in its ``Makefile``.

``--today None`` makes a report with no date, which relies only on the data:

- Nothing is marked as today on the charts
- Forecasts start from each task's latest status update, however long ago that was, and the burncharts from the \
  latest update of their tasks
- Stale tasks, the current milestone and availability are checked against the latest status update in the input, \
  instead of today. The *available today* column of the resources is called *available at latest update*

The line under the title of every page gives the report date, or says there is none and gives the latest status \
update. A date that cannot be read, e.g. ``--today 2026-02-30``, is reported as an error.

.. image:: /images/report_overview.png
   :align: center

.. note::

    The report is static HTML and needs no server. The charting and table libraries are loaded from \
    their public CDNs, so an internet connection is required to view it.

Errors and Warnings
-------------------

The input files are checked before any of the report is written. If a problem is found the script stops \
with a single line describing it, and exits with a non-zero status so that it can be used in a CI job:

.. code-block:: text

    ERROR : tasks definitions contain unexpected fields: 'descripton' in ALU. Expected fields are: ...

Errors are raised for files that are not valid YAML, definitions with no name, names defined more than \
once, unexpected (usually misspelt) fields, and tasks or workpackages with no status updates or allocations. \
Each input page lists the mistakes caught for its type, e.g. effort in an unknown unit or a task resource \
that is not defined, under *Mistakes that are caught*.

Files whose ``type`` is not recognised are skipped with a warning, as is an input directory with no input files:

.. code-block:: text

    WARNING : plan/tasks.yaml: unknown type 'task_definitions' - file ignored. Expected one of: ...

Any of the input types may be left out. The report is still generated, and the pages for anything \
not yet defined say so. A plan can therefore be built up a file at a time.

The title, logo, colours and fonts of the report can be changed with YAML files in the input directory, \
and the theme chooser at the top right of every page lists the themes available. See :doc:`format`.

Checking the input
------------------

``--check`` reads and validates the input in exactly the same way as when a report is generated, but stops \
there. Nothing is written, so it is quick and can be used before a commit or in a CI job:

.. code-block:: text

    $ apheleia_project_report --check --input plan
    OK : input checked, no problems found (11 milestones, 3 resources, 2 projects, 3 workpackages, 4 tasks)

If a problem is found the ``ERROR :`` line described above is printed and the exit status is 1. Warnings are still \
printed. The exit status is 0 if the input is valid, whatever the warnings.

Report Structure
----------------

The output directory contains a top level ``index.html`` and a directory for each type of definition. \
Each directory contains an ``index.html`` giving an overview of every item of that type, and one page per item.

.. code-block:: text

    html
    ├── index.html
    ├── milestones
    │   ├── index.html
    │   └── m0.html
    ├── projects
    │   ├── index.html
    │   └── project_alpha.html
    ├── resources
    │   ├── index.html
    │   └── mickey_mouse.html
    ├── tasks
    │   ├── index.html
    │   └── instruction_fetch.html
    └── workpackages
        ├── index.html
        └── cpu_development.html

The top level ``index.html`` has a tab for each of projects, resources and milestones. Workpackages and \
tasks are reached by following links from their project, workpackage or resource.

Navigation
----------

Every name shown in a table, and every bar or segment in a chart, links to the page for that item. \
Clicking through allows the plan to be explored from the top down, for example from a project to one of \
its workpackages, to a task within it, or across from a workpackage to a resource allocated to it.

Hovering over the information badge next to a chart or table title gives a description of what it shows.

Charts with a time axis can be switched between monthly, quarterly and yearly scale.

Every project, workpackage and task page starts with the same three tabs:

- **Summary** - the status of the item and the checks that apply to it
- **Timeline** - when it runs, with today (if the report has a date) and its milestones marked
- **Burnchart** - a burndown and a burnup of its tasks, and when the remaining effort is forecast to be done

Burncharts
----------

The burnchart tab adds up the effort spent and remaining of the tasks from their status updates. The **burndown** \
shows the effort remaining over time; the **burnup** shows the effort spent against the total effort (spent + \
remaining), so a rising total shows work being added or re-estimated. A task counts from its first status update, \
so to see the whole plan from the start, give each task a first update with nothing spent at the start of the project.

While work remains, the dashed lines forecast it from the latest status update, or today if that is later and the \
report has a date (see `Report date`_), at the rate the resources are allocated:

- An allocation of 1.0 does one day of effort every working day, so the forecast is a straight line through each \
  period of allocation, and flat where nothing is allocated
- Each workpackage is forecast with its own allocation, so people allocated to one workpackage never do the work \
  of another. A project's forecast adds up those of its workpackages, and ends when the last of them does
- A task is forecast with an equal share of its resources' allocation to its workpackage, shared with their other \
  unfinished tasks in that workpackage
- The **estimated end** is the working day the allocated effort first covers the effort remaining. If the \
  allocation runs out first, the forecast carries on at the average allocated rate and the end is marked \
  *beyond allocation*. If work remains in a workpackage with no allocation left, the end shows *No allocation*

The Burn Summary above the charts gives the estimated end date, progress, effort spent and remaining, when the \
allocation ends, the latest update and, if there is one, the date the work should be done by: the project end for a \
project and the milestone for a workpackage. The estimated end is highlighted when it is beyond the allocation or \
after that date.

.. image:: /images/project_burndown.png
   :align: center

.. image:: /images/project_burnup.png
   :align: center

Pages
-----

Projects
^^^^^^^^

- **Overview** - timeline of all projects, and a table of their definitions
- **Project** - a summary of the status of its tasks grouped by the milestone they are needed for, the \
  tasks that are over their estimate or stale, the workpackages outside their milestone, over their estimate or \
  whose tasks need more than they are allocated, and the months its resources are over allocated; the \
  project timeline with its milestones marked; its burndown and burnup with the forecast end date; the timeline and \
  resource allocation of its workpackages; and its definition

.. image:: /images/project_timeline.png
   :align: center

Workpackages
^^^^^^^^^^^^

- **Overview** - timeline of all workpackages, the effort allocated to each over time, a summary table, and \
  the effort of their tasks against their allocation and estimate
- **Workpackage** - its milestone, estimate and task effort checks and the progress of its tasks, with those over \
  their estimate or stale; the timeline of the workpackage and its tasks; its burndown and burnup with the forecast \
  end date; effort allocated by resource; and the progress of each task

.. image:: /images/workpackage_timeline.png
   :align: center

.. image:: /images/workpackage_allocations.png
   :align: center

.. image:: /images/task_progress_by_task.png
   :align: center

Resources
^^^^^^^^^

- **Overview** - when every resource is available and at what percentage, the number of full time \
  equivalent resources available over time, how much of each resource's available time is allocated each month \
  and the months they are over allocated, each resource's availability today, and every availability period
- **Resource** - their availability periods, effort allocated by project and by workpackage against the time \
  they have available, the months they are over allocated, the progress of their tasks (including tasks they \
  share with others) with those over their estimate or stale, and their definition. See :doc:`../inputs/resources` for how to read the availability charts

.. image:: /images/resource_availability.png
   :align: center

.. image:: /images/resources_over_time.png
   :align: center

.. image:: /images/resource_allocations.png
   :align: center

Tasks
^^^^^

- **Overview** - timeline of all tasks, a summary table, the tasks over their estimate, the stale tasks and \
  overall progress
- **Task** - its latest status, whether it is within its estimate and how long ago it was updated; the task \
  timeline; and its burndown and burnup with the forecast end date

.. image:: /images/task_summary.png
   :align: center

.. image:: /images/task_timeline.png
   :align: center

Milestones
^^^^^^^^^^

- **Overview** - every milestone, the projects it is the current milestone for, and when it is next due
- **Milestone** - every project that has dated the milestone, with its start (for windows) and end dates, \
  whether it has passed, is current or is upcoming, and the milestone's definition. See \
  :doc:`../inputs/milestones` for how milestones are dated

All timelines mark today's date, unless the report has no date. On the charts allocations are shown in person-months and task effort in days. \
Tables of effort have a *Units* select box to show it in man-years, man-months, man-weeks or man-days. See :doc:`workpackages <../inputs/workpackages>` and :doc:`tasks <../inputs/tasks>` for how these are calculated.

Using in a Makefile
-------------------

Each example contains a ``Makefile`` that can be copied into your own plan directory:

.. literalinclude:: ../../../examples/simple/Makefile
    :language: make
