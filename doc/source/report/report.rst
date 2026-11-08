.. _report:

Generating Reports
==================

Overview
--------

Apheleia Project Management provides a simple script to generate the report in HTML format. The script is \
exported as a project script and added to your path automatically when the package is installed. \
To generate a report, run the script with the following command:

.. code-block:: shell

    $ apheleia_project_report --input <input directory> --html <output directory>

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

Open ``index.html`` in the output directory in a browser to view the report.

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

Pages
-----

Projects
^^^^^^^^

- **Overview** - timeline of all projects, and a table of their definitions
- **Project** - a summary of the status of its tasks grouped by the milestone they are needed for, the \
  tasks that are over their estimate or stale, the workpackages outside their milestone, over their estimate or \
  whose tasks need more than they are allocated, and the months its resources are over allocated; the \
  project timeline with its milestones marked; the timeline and \
  resource allocation of its workpackages; and its definition

.. image:: /images/project_timeline.png
   :align: center

Workpackages
^^^^^^^^^^^^

- **Overview** - timeline of all workpackages, the effort allocated to each over time, a summary table, and \
  the effort of their tasks against their allocation and estimate
- **Workpackage** - workpackage timeline, effort allocated by resource, and the effort, progress, timeline and \
  forecast completion of its tasks, with those over their estimate or stale

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
- **Task** - task timeline, its latest status, whether it is within its estimate and how long ago it was \
  updated, and its progress over time

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

All timelines mark today's date. On the charts allocations are shown in person-months and task effort in days. \
Tables of effort have a *Units* select box to show it in man-years, man-months, man-weeks or man-days. See :doc:`workpackages <../inputs/workpackages>` and :doc:`tasks <../inputs/tasks>` for how these are calculated.

Using in a Makefile
-------------------

Each example contains a ``Makefile`` that can be copied into your own plan directory:

.. literalinclude:: ../../../examples/simple/Makefile
    :language: make
