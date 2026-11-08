.. _workpackages:

Workpackages
============

Overview
--------

Workpackages break a :doc:`project <projects>` into areas of work, and record which :doc:`resources <resources>` \
are allocated to that work and when. They describe the plan: how much effort is expected to be spent.

Progress against the plan is recorded by :doc:`tasks <tasks>`.

Fields
------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``workpackage``
     - Yes
     - Name of the workpackage
   * - ``project``
     - Yes
     - Name of the project this workpackage belongs to
   * - ``description``
     - No
     - Description of the workpackage
   * - ``milestone``
     - No
     - Milestone the workpackage is working towards, see below
   * - ``estimate``
     - No
     - Original estimate of the effort for the workpackage, e.g. ``5 mm``, see below
   * - ``allocations``
     - Yes
     - List of resource allocations, see below

No other fields are permitted.

Allocations
-----------

Each entry in ``allocations`` has:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``start``
     - Yes
     - First month of the allocation
   * - ``end``
     - Yes
     - Last month of the allocation
   * - ``resource``
     - Yes
     - Name of a resource defined in a :doc:`resources <resources>` file
   * - ``allocation``
     - Yes
     - Fraction of the resource's time allocated, where ``1.0`` is full time and ``0.5`` is half time

Allocations are made in whole months, and both the ``start`` and ``end`` months are included. Dates are \
most naturally written as ``YYYY-MM``.

The effort of an allocation is measured in person-months:

.. code-block:: text

    effort = allocation x number of months

For example an allocation of ``0.5`` from ``2026-07`` to ``2026-09`` is 3 months at half time, or 1.5 person-months.

A resource can have several allocations to the same workpackage, for example to vary their allocation over \
time, and can be allocated to many workpackages at once. The start and end of the workpackage are taken \
from the earliest and latest of its allocations.

Milestones
----------

A workpackage can be associated with a :doc:`milestone <milestones>` using ``milestone``. The workpackage must \
end by the date the project gives this milestone, compared to the month. Starting before the previous milestone \
is fine.

Workpackages that end after their milestone, or whose milestone has no date in the project, are marked \
``OUTSIDE MILESTONE`` with the reason in the workpackage tables, and listed under *Workpackages Outside Milestone* \
on the project summary. Workpackages with no ``milestone`` are not checked.

Estimates
---------

A workpackage can be given the effort it was originally estimated at using ``estimate``: a number followed by a unit.

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Unit
     - Meaning
     - Equivalent
   * - ``md``
     - Man-days
     - 20 man-days is 1 man-month
   * - ``mw``
     - Man-weeks
     - 5 man-days is 1 man-week, or 4 man-weeks is 1 man-month
   * - ``mm``
     - Man-months
     - The unit of allocated effort
   * - ``my``
     - Man-years
     - 1 man-year is 12 man-months

Spaces are optional and the unit is not case sensitive, so ``5 mm``, ``5mm`` and ``5 MM`` are the same. The number \
can have decimals, e.g. ``2.5 mm``.

The report adds up the effort allocated to the workpackage (allocation x months, over all its allocations) and \
compares it with the estimate. A workpackage allocated more than its estimate is marked ``OVER ESTIMATE`` in red, \
with how far over it is, in the workpackage tables and its own page, and listed under *Workpackages Over Estimate* \
on the project summary. A workpackage within its estimate shows how much of it is allocated, and one with no \
``estimate`` is not checked.

Every table of workpackages has a *Units* select box, to show effort in man-years (``my``), man-months (``mm``, \
the default), man-weeks (``mw``) or man-days (``md``). It changes the effort, estimate and allocated columns and \
the messages in them, on every table on the page, and is remembered by the browser for other pages.

Task Effort
-----------

The tasks of a workpackage (those that give its name as their ``workpackage``, see :doc:`tasks`) are checked \
against the workpackage:

Task forecast against the allocation
    The effort spent plus the effort remaining of all its tasks is what they are now expected to need. If it is \
    more than the effort allocated to the workpackage, the workpackage is marked ``TASKS OVER ALLOCATION`` with \
    how much more is needed. This catches workpackages whose tasks have grown, or that have more tasks than were \
    planned for, before the allocation runs out.

Task estimates against the estimate
    The original estimates of its tasks are added up. If the workpackage has an ``estimate`` and they come to \
    more than it, the workpackage is marked ``TASKS OVER ESTIMATE``: the work was broken down into more than \
    was estimated for it.

Tasks with no estimate add nothing to the task estimates, so the number of them is shown alongside. A \
workpackage with no tasks is not checked.

The checks are shown in a *Task Effort* table on the workpackages overview, the *Workpackages* tab of each \
project and the *Tasks* tab of each workpackage, and the workpackages that fail either check are listed under \
*Workpackages Over Task Effort* on the project summary. The table has a *Units* select box like every other \
table of effort.

Mistakes that are caught
------------------------

An estimate that cannot be understood stops the report with a message starting ``ERROR :`` naming the workpackage, \
and no report is produced.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - How to fix it
   * - A number with no unit, such as ``"5"`` or ``5``
     - Add a unit, e.g. ``"5 mm"``
   * - An unknown unit, such as ``weeks``
     - Use ``md``, ``mw``, ``mm`` or ``my``
   * - Something that is not a number, such as ``"lots mm"``
     - Write a number followed by a unit
   * - An estimate of zero or less
     - Use an estimate greater than 0, or remove it

The ``examples/workpackages/errors`` directory has a small example of each of these.

Example
-------

.. literalinclude:: ../../../examples/simple/workpackages.yaml
    :language: yaml

The effort allocated to a project's workpackages, stacked by resource:

.. image:: /images/workpackage_allocations.png
   :align: center

The ``workpackages/estimates`` example has a workpackage with no estimate, one with a generous estimate, one with \
a low estimate (so it is over) and one allocated exactly its estimate:

.. literalinclude:: ../../../examples/workpackages/estimates/workpackages.yaml
    :language: yaml

The ``workpackages/task_effort`` example has a workpackage whose tasks fit, one whose tasks need more than is \
allocated, one whose task estimates add up to more than its estimate, one with a task with no estimate and one \
with no tasks:

.. literalinclude:: ../../../examples/workpackages/task_effort/workpackages.yaml
    :language: yaml
