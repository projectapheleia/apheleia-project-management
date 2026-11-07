.. _tasks:

Tasks
=====

Overview
--------

Tasks are the individual pieces of work within a :doc:`workpackage <workpackages>`, each owned by a single \
:doc:`resource <resources>`. Where workpackages describe the plan, tasks record what has actually happened.

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
     - Name of the resource working on this task
   * - ``description``
     - No
     - Description of the task
   * - ``start``
     - No
     - Date the task starts. If not given it defaults to the previous milestone, see below
   * - ``estimate``
     - No
     - Original estimate of the effort for the task, in days. Tasks without an estimate are flagged in the report
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
     - Total effort spent on the task up to this date, in days
   * - ``remaining``
     - Yes
     - Estimated effort remaining, in days. ``0`` means the task is complete

``spent`` is the running total, not the effort spent since the last update.

To update a task add a new entry to the end of its ``status`` list. The first entry is normally the date the \
task starts, with ``spent: 0`` and ``remaining`` set to the initial estimate.

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
- A task is **past its estimate** if the variance is greater than zero

In the *Progress by Task* chart each bar is split at the estimate, which is marked with a black line. \
Effort within the estimate is blue and effort past it is red, so a task that is on track is all blue and a \
late one ends in red - light red if the overrun is still to be done, dark red once it has been spent.

Tasks past their estimate are listed, worst first, on the project page. A task with no estimate is shown \
as *MISSING* and cannot be checked, so it is best to give every task an estimate.

Progress and Forecasts
----------------------

Task progress is derived from the latest status update:

- **Status** is *Not started* if nothing has been spent, *Complete* if nothing remains, and *In progress* otherwise
- **% complete** is ``spent / (spent + remaining)``
- **Forecast end** is the date of the latest status update plus the remaining effort in working days. \
  If the task is not complete, the forecast is made from today if the latest update is in the past, and from \
  the start date if the task has not yet started, so an unfinished task is never forecast to finish in the past

Tasks have no milestone of their own. On the project page each task is counted against the first milestone \
dated on or after its forecast end - the milestone it is needed by. Tasks forecast to finish after the last \
milestone are listed separately.

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
