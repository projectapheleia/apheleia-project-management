.. _resources:

Resources
=========

Overview
--------

A **resource** is a person (or a team) who can work on your projects. For each resource you say:

- **who** they are - a name, and optionally a user name and a link to a profile page
- **when** they can work - the dates they are available
- **how much** they can work - the percentage of their time they are available, for example ``100`` for full \
  time or ``50`` for half time

Apheleia uses this to show when each person can work, and how many people you can call on in each month, \
quarter or year. Holidays, parental leave, part time working, people joining late and people leaving are all \
covered.

Resources are linked to the rest of the plan by name: :doc:`workpackage allocations <workpackages>` and \
:doc:`tasks <tasks>` refer to a resource using exactly the same ``resource`` name, including capitals and spaces.

The simplest resource
---------------------

Only a name is needed. A resource with no dates is assumed to be available full time, all of the time:

.. code-block:: yaml

    type: "resources_definitions"
    data:
      - resource: "Ivy Chen"

Most resources also say when they start, and perhaps when they finish:

.. code-block:: yaml

      - resource: "Eve Morgan"
        uname: "emorgan"
        start: "2024-01-01"
        end: "2026-06-30"

A resource with no ``end`` is assumed to be available for as long as the charts run.

Fields
------

These are the fields you can give for each resource:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - What it means
   * - ``resource``
     - Yes
     - The resource's name. Must be unique, and is how other files refer to this resource
   * - ``uname``
     - No
     - A short user name, for example a login or email alias
   * - ``profile``
     - No
     - A link to more information about the resource, for example a staff page
   * - ``start``
     - No
     - The first day they are available
   * - ``end``
     - No
     - The last day they are available. Leave it out if there is no end date
   * - ``availability``
     - No
     - The percentage of their time available, from ``0`` to ``100``. Leave it out for ``100`` (full time)
   * - ``periods``
     - No
     - A list of periods, for when availability changes over time. See :ref:`resource-periods` below

Any other field is reported as an error. This catches spelling mistakes, such as ``availabilty``.

Use **either** ``start`` / ``end`` / ``availability`` **or** ``periods`` for a resource, not both.

Part time resources
-------------------

Add ``availability`` to say what percentage of their time a resource can give. If it is left out it is \
``100``, meaning full time.

.. code-block:: yaml

      # Works three days out of five
      - resource: "Ben Carter"
        start: "2025-06-01"
        availability: 60

Any number from ``0`` to ``100`` can be used, including decimals such as ``37.5``. Writing ``"60%"`` also works.

.. _resource-periods:

When availability changes: periods
-----------------------------------

People's availability is rarely the same for the whole of a project. They take leave, change their hours, or \
leave and come back. To describe this, give a list of ``periods`` instead of a single ``start`` and ``end``. \
Each period is a stretch of time with its own availability:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - What it means
   * - ``start``
     - No
     - The first day of the period. Only the earliest period can leave this out
   * - ``end``
     - No
     - The last day of the period. Only the latest period can leave this out, meaning it carries on with no end date
   * - ``availability``
     - No
     - The percentage of their time available during the period, from ``0`` to ``100``. Leave it out for ``100``

For example, someone who works full time, takes two weeks off, then comes back at half time:

.. code-block:: yaml

      - resource: "Mickey Mouse"
        periods:
          - start: "2024-01-01"
            end: "2025-07-31"
          - start: "2025-08-01"
            end: "2025-08-14"
            availability: 0
          - start: "2025-08-15"
            end: "2026-06-01"
            availability: 50

How periods work
^^^^^^^^^^^^^^^^

- **Start and end days are both included.** A period from ``2025-08-01`` to ``2025-08-14`` covers 14 days.
- **Periods must not overlap.** Each day can only belong to one period. If the next period starts on the day \
  after the previous one ends, there is no gap.
- **Gaps mean "not available".** Any day not covered by a period is a day the resource cannot work.
- **Order does not matter.** Periods are sorted by date for you, so you can add a new one at the top or bottom.

Recording leave
^^^^^^^^^^^^^^^

There are two ways to record time off, and both give the same result in the charts:

**As a gap** - end one period before the leave, and start the next one after it:

.. code-block:: yaml

        periods:
          - start: "2025-01-01"
            end: "2026-10-31"
          # November off
          - start: "2026-12-01"

**As a period at 0%** - this makes the leave visible as its own (faint) bar on the charts and in the tables, \
which can be clearer for other readers:

.. code-block:: yaml

        periods:
          - start: "2025-01-01"
            end: "2026-10-31"
          - start: "2026-11-01"
            end: "2026-11-30"
            availability: 0
          - start: "2026-12-01"

Common situations
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Situation
     - How to write it
   * - Full time, no end date
     - ``start`` only
   * - Part time throughout
     - ``start`` and ``availability``
   * - Fixed term contract
     - ``start`` and ``end``
   * - Has left the team
     - ``start`` and an ``end`` in the past
   * - Joins in the future
     - ``start`` in the future
   * - Holiday or leave
     - A gap between two periods, or a period with ``availability: 0``
   * - Changes hours
     - One period for each set of hours, the second starting the day after the first ends
   * - Phased return after leave
     - A period at ``0``, then periods stepping up, for example ``40``, ``70``, then ``100``

Writing dates
-------------

Write dates as ``YYYY-MM-DD``, for example ``"2026-03-31"``. Putting them in quotes is recommended but not required.

A date written as just a month, such as ``"2026-03"``, means the **first** day of that month. This is fine for a \
``start``, but for an ``end`` it is usually not what you want: ``end: "2026-03"`` stops on 1 March, not 31 March. \
Write the full date for end dates.

``None``, ``null`` or an empty value means "no date".

Mistakes that are caught
------------------------

If a resource cannot be understood, the report stops with a message starting ``ERROR :`` that names the resource \
and the problem, and no report is produced. Fix the input and run it again.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - How to fix it
   * - Two periods overlap
     - Move the start of the later period to the day after the earlier one ends
   * - A period ends before it starts
     - Check the dates have not been swapped or mistyped
   * - Availability is below ``0`` or above ``100``
     - Use a percentage, for example ``50`` rather than ``0.5`` or ``150``
   * - A period other than the latest has no ``end``
     - Add the ``end``. Only the latest period can carry on with no end date
   * - A period other than the earliest has no ``start``
     - Add the ``start``
   * - ``periods`` given together with ``start``, ``end`` or ``availability``
     - Move the dates into the list of periods, or remove ``periods``
   * - ``periods`` is empty
     - Add at least one period, or remove ``periods``
   * - A date cannot be read
     - Write it as ``YYYY-MM-DD``, and check the month and day exist
   * - An unexpected field
     - Check the spelling. The allowed fields are listed above
   * - Two resources have the same name
     - Give each resource a unique name

The ``examples/resources/errors`` directory has a small example of each of these.

What you see in the report
--------------------------

Resources have an overview page, and a page for each resource.

Availability chart
    One row per resource, with one bar for each period. A bar's strength shows how available they are: a full \
    time period is solid, a half time period is lighter, and leave at 0% is faint. Gaps between bars are times \
    the resource is not available. Hover over a bar to see its dates and percentage. The red dashed line marks today.

Resources Available Over Time
    A bar for each month, quarter or year showing how many people are available, counted as **full time \
    equivalents**. Each person counts for the share of the time they are available:

    - someone full time for the whole month counts as **1**
    - someone at 50% for the whole month counts as **0.5**
    - someone full time who is on leave for half the month also counts as about **0.5**

    The number above each bar is the total. Each coloured block is one person, and clicking it opens their page.

Resources table
    One row per resource, with the first and last dates they are available, how many periods they have, and \
    their availability today. **Available today** shows ``0%`` for someone who is on leave in a 0% period, and \
    ``0% (no active period)`` for someone who has left, has not started yet, or is in a gap between periods.

Availability Periods table
    Every period of every resource, with its dates and percentage.

Each resource's own page also shows the projects and workpackages they are allocated to, and the progress of \
their tasks.

Examples
--------

The ``simple`` example has three resources: one with leave and a move to half time, one with a single open \
ended period, and one with a month's leave as a gap:

.. literalinclude:: ../../../examples/simple/resources.yaml
    :language: yaml

The availability of each resource:

.. image:: /images/resource_availability.png
   :align: center

The ``resources/availability`` example has a wider mix: people who are working today at different \
percentages, someone on leave, people who have left, are yet to start or are between periods, and a resource \
with no dates at all. Each resource has a comment explaining its situation:

.. literalinclude:: ../../../examples/resources/availability/resources.yaml
    :language: yaml
