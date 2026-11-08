.. _tasks:

Tasks
=====

Overview
--------

Tasks are the individual pieces of work within a :doc:`workpackage <workpackages>`, each done by one \
:doc:`resource <resources>` or shared by several. Where workpackages describe the plan, tasks record what has \
actually happened.

Each task carries a history of status updates. Each update records the effort spent so far and the effort \
estimated to remain. Keeping the history, rather than overwriting it, allows progress to be charted over \
time and shows how estimates have changed.

Fields
------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``task``
     - Yes
     - Name of the task
   * - ``project``
     - Yes
     - Name of the project this task belongs to
   * - ``workpackage``
     - Yes
     - Name of the workpackage this task belongs to
   * - ``resource``
     - Yes
     - Name of the resource working on this task, or a list of names for a task shared by several people. Each \
       must be defined in the :doc:`resources <resources>`. See `Shared Tasks`_
   * - ``description``
     - No
     - Description of the task
   * - ``start``
     - No
     - Date the task starts. If not given it defaults to the previous milestone, see below
   * - ``estimate``
     - No
     - Original estimate of the effort for the task, e.g. ``"3 mw"``. See `Effort`_. Tasks without an estimate are \
       flagged in the report
   * - ``status``
     - Yes
     - List of status updates, see below

No other fields are permitted.

Status
------

Each entry in ``status`` has:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``date``
     - Yes
     - Date of the status update
   * - ``spent``
     - Yes
     - Total effort spent on the task up to this date, e.g. ``"4 md"``. See `Effort`_
   * - ``remaining``
     - Yes
     - Estimated effort remaining, e.g. ``"1.5 mw"``. ``0`` means the task is complete

No other fields are permitted. A unit is given with each value, not as a field of its own.

``spent`` is the running total, not the effort spent since the last update.

To update a task add a new entry to the end of its ``status`` list. The first entry is normally the date the \
task starts, with ``spent: 0`` and ``remaining`` set to the initial estimate.

Effort
------

The ``estimate``, and ``spent`` and ``remaining`` in each status update, are written in the same way as a \
:doc:`workpackage estimate <workpackages>`: a number followed by a unit.

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Unit
     - Meaning
     - Equivalent
   * - ``md``
     - Man-days
     - The unit used for forecasts, which count working days
   * - ``mw``
     - Man-weeks
     - 1 man-week is 5 man-days
   * - ``mm``
     - Man-months
     - 1 man-month is 20 man-days, or 4 man-weeks
   * - ``my``
     - Man-years
     - 1 man-year is 12 man-months

Spaces are optional and the unit is not case sensitive, so ``3 mw``, ``3mw`` and ``3 MW`` are the same. The number \
can have decimals, e.g. ``0.5 mm``. Units can be mixed freely, even within one status update:

.. code-block:: yaml

    estimate: "3 mw"
    status:
      - date: "2026-10-05"
        spent: 0
        remaining: "3 mw"
      - date: "2026-11-02"
        spent: "8 md"
        remaining: "1.4 mw"

The default unit
^^^^^^^^^^^^^^^^

Unlike a workpackage estimate, task effort can be a plain number, such as ``spent: 3``. A plain number is in the \
default unit, ``task_unit``, which is man-days (``md``) unless a ``format_definitions`` file changes it. It applies \
to every task in the input, and to the estimate as well as the status updates:

.. code-block:: yaml

    type: "format_definitions"
    data:
      task_unit: "mw"     # spent: 3 now means 3 man-weeks

Effort given with a unit is not affected, so ``spent: "3 md"`` is 3 man-days whatever ``task_unit`` is. See \
:doc:`../report/format`.

In the report
^^^^^^^^^^^^^

Every table of tasks has a *Units* select box, the same as the workpackage tables, which shows the estimate, \
spent, remaining and variance, and the messages about them, in man-years, man-months (the default), man-weeks or \
man-days. The charts show task effort in days.

Shared Tasks
------------

A task shared by several people gives a list of names as its ``resource``:

.. code-block:: yaml

    - task: "Board Bring-up"
      project: "Project Shared"
      workpackage: "Bring-up"
      resource:
        - "Mickey Mouse"
        - "Daffy Duck"
      estimate: "2 mw"

``resource: ["Mickey Mouse", "Daffy Duck"]`` is the same. A list of one name is the same as the name.

The ``estimate``, ``spent`` and ``remaining`` are for the task as a whole: the effort of everyone working on it, \
not of each person. The report does not divide them between the people. A shared task is shown, in full, on the \
*Tasks* tab of the page of each of its resources, and the ``resource`` column of the task tables links to each \
of them.

Every name must be a resource defined in the input, and no name can be listed twice.

Start Dates
-----------

If ``start`` is not given it defaults to the date of the previous milestone: the latest of the project's \
:doc:`milestones <projects>` dated on or before the task's first status update. If the project has no such \
milestone the project start date is used, and failing that the date of the first status update. The report \
notes where a start date has been defaulted.

Estimates
---------

``estimate`` is the original estimate and is never changed once set. Comparing it with the current \
``spent + remaining`` shows how the estimate has moved:

- **Variance** is ``spent + remaining - estimate``
- A task is **over its estimate** if the variance is greater than zero, even if the extra effort has not been \
  spent yet

In the *Progress by Task* chart each bar is split at the estimate, which is marked with a black line. \
Effort within the estimate is blue and effort past it is red, so a task that is on track is all blue and a \
late one ends in red - light red if the overrun is still to be done, dark red once it has been spent.

Over estimate tasks are highlighted wherever tasks are shown:

- The *estimate check* column of every task table marks the task ``OVER ESTIMATE`` in red with how far over it \
  is, and says which of these it is:

  - *spent + remaining ... is over the estimate*: the over-run is forecast, but has not been spent yet
  - *already spent ..., past the estimate*: the effort spent alone is more than the estimate, and there is more to do
  - *finished in ...*: the task is complete, and took more than its estimate

  A task within its estimate shows how much of it is used, e.g. *Within estimate 0.75 mm of 1 mm (75%)*.
- The *variance* column shows the amount over in a red badge.
- *Tasks Over Estimate* lists them, worst first by percentage over, on the project summary, the tasks page, and \
  the *Tasks* tab of each workpackage and resource.
- The *Task Progress Summary* counts them, and the *Task Status by Milestone* table on the project page counts \
  them, with the total over, for each milestone.

A task can be over its estimate before it has started, if its first status update already gives more remaining \
than the estimate. A task with no estimate is shown as *MISSING* and cannot be checked, so it is best to give \
every task an estimate.

Progress and Forecasts
----------------------

Task progress is derived from the latest status update:

- **Status** is *Not started* if nothing has been spent, *Complete* if nothing remains, and *In progress* otherwise
- **% complete** is ``spent / (spent + remaining)``
- **Forecast end** is the date of the latest status update plus the remaining effort in working days, rounded \
  up to a whole day. \
  If the task is not complete, the forecast is made from today if the latest update is in the past, and from \
  the start date if the task has not yet started, so an unfinished task is never forecast to finish in the past. \
  If the report has no date (``--today None``, see :doc:`../report/report`) it is made from the latest update

Tasks have no milestone of their own. On the project page each task is counted against the first milestone \
dated on or after its forecast end - the milestone it is needed by. Tasks forecast to finish after the last \
milestone are listed separately.

Stale Tasks
-----------

Progress and forecasts are only as good as the latest status update. An unfinished task whose latest update is \
more than ``stale_days`` calendar days before the report date (``--today``, see :doc:`../report/report`) is \
marked ``STALE``. If the report has no date, the latest status update in the input is used instead. ``stale_days`` is \
set in the format (see :doc:`../report/format`) and is 14 by default:

.. code-block:: yaml

    type: "format_definitions"
    data:
      stale_days: 30

Complete tasks are never stale. Set ``stale_days: null`` to turn the check off.

In the report:

- Every task table has an *update check* column saying how long ago the task was last updated, with a red \
  ``STALE`` badge for stale tasks.
- *Stale Tasks* lists them, the longest without an update first, on the project summary, the tasks page, and \
  the *Tasks* tab of each workpackage and resource.
- The *Task Progress Summary* counts them, and the *Task Status by Milestone* table counts them for each milestone.

Whether a task is stale depends on the report date, which is the day the report is run unless ``--today`` gives \
one, so a report made later can show tasks as stale that were not before.

Mistakes that are caught
------------------------

``stale_days`` in the format must be a whole number of days, 1 or more, or ``null``. Anything else, such as \
``"two weeks"`` or ``0``, is reported as an error.

A task that cannot be understood stops the report with a message starting ``ERROR :`` naming the task, and no \
report is produced.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - How to fix it
   * - An unknown unit, such as ``"40 hours"`` or ``spent: "6 hours"``
     - Use ``md``, ``mw``, ``mm`` or ``my``
   * - Effort that is not a number, such as ``"about a week"``
     - Write a number, optionally followed by a unit
   * - An estimate of zero or less
     - Use an estimate greater than 0, or remove it
   * - Negative ``spent`` or ``remaining``
     - Use 0 or more
   * - A status update with no ``date``, ``spent`` or ``remaining``
     - Give all three
   * - A status update date that cannot be read, such as ``2026-02-30``
     - Use a real date, written ``YYYY-MM-DD``
   * - Two status updates on the same date
     - Combine them, or correct the date
   * - A unit given as a field, such as ``unit: "mw"``
     - Give the unit with the value instead, e.g. ``spent: "2 mw"``
   * - A task with no status updates
     - Add at least one, normally ``spent: 0`` and ``remaining`` set to the estimate
   * - No ``resource``, or an empty list of resources
     - Name at least one resource
   * - The same resource listed twice
     - Remove the repeat
   * - A resource that is not defined, often a misspelling such as ``Dafy Duck``
     - Correct the name, or add the resource to the resources
   * - A ``task_unit`` that is not ``md``, ``mw``, ``mm`` or ``my``
     - Correct it in the ``format_definitions`` file

The ``examples/tasks/errors`` directory has a small example of each of these.

Example
-------

.. literalinclude:: ../../../examples/simple/tasks.yaml
    :language: yaml

The progress of these tasks as shown on the *CPU Development* workpackage page:

.. image:: /images/task_summary.png
   :align: center

.. image:: /images/task_progress_by_task.png
   :align: center

.. image:: /images/task_timeline.png
   :align: center

The ``tasks`` examples show good and bad estimates (``estimates``), shared tasks (``shared``), effort in every \
unit (``units``) and a different default unit (``default_unit``):

.. literalinclude:: ../../../examples/tasks/estimates/tasks.yaml
    :language: yaml

.. literalinclude:: ../../../examples/tasks/shared/tasks.yaml
    :language: yaml
