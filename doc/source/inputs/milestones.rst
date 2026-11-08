.. _milestones:

Milestones
==========

Overview
--------

A **milestone** is a named checkpoint in a project, for example *Design Review*, *Tape-out* or *Release*.

Milestones are set up in two steps:

1. **Name them once**, in a milestones file. This is the shared list that every project picks from.
2. **Date them in each project**, in the :doc:`projects <projects>` file. Each project gives a milestone its own \
   date, because the same checkpoint happens at different times on different projects.

Keeping the names separate from the dates means every project uses the same set of checkpoints. That makes it \
easy to compare projects like for like: you can see at a glance which projects have passed *Design Review* and \
which are still working towards it.

A project can date a milestone in three ways:

- **With a due date only**, when all that matters is the date it must be delivered by, for example \
  *Release by 15 December*
- **As a window** with a start and an end, when how long the milestone takes matters too, for example \
  *beta testing from March to April*
- **Relative to another milestone**, for example "six weeks after the design review"

Step 1: naming milestones
-------------------------

A milestones file lists each milestone with a name and, optionally, a description:

.. code-block:: yaml

    type: "milestones_definitions"
    data:
      - milestone: "M1"
        description: "Design Review"

      - milestone: "M2"
        description: "Beta Testing"

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - What it means
   * - ``milestone``
     - Yes
     - The milestone's name. Must be unique. Short names such as ``M1`` work well, and are never mistaken for dates
   * - ``description``
     - No
     - What the milestone is, shown when hovering and in tables

No other fields are allowed. In particular a milestone has **no date here** - dates are given by each project.

Step 2: dating milestones in a project
--------------------------------------

Each project lists the milestones that apply to it under ``milestones``, and gives each one its dates:

.. code-block:: yaml

    type: "projects_definitions"
    data:
      - project: "Project Alpha"
        milestones:
          - milestone: "M1"
            date: "2026-02-01"
          - milestone: "M2"
            start: "2026-03-01"
            end: "2026-04-30"

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - What it means
   * - ``milestone``
     - Yes
     - The name of a milestone from the milestones file
   * - ``date``
     - See below
     - The date the milestone is due, when only the delivery date matters
   * - ``start``
     - See below
     - The day a milestone window opens
   * - ``end``
     - See below
     - The day a milestone window closes. This is the day the milestone is due

Give a milestone **either** a ``date`` **or** both a ``start`` and an ``end``. Don't mix them, and don't give \
only one of ``start`` and ``end``.

A project does not have to use every milestone, and each milestone can only be listed once per project.

Milestones with a due date
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``date`` when only the delivery date is important, not how long the milestone takes. The work towards it \
can go on for as long as it needs to; what matters is that the milestone is reached by this date:

.. code-block:: yaml

          # The release must be delivered by 15 December
          - milestone: "M4"
            date: "2026-12-15"

This is the most common kind of milestone. On the project timeline it is drawn as a **dashed red vertical line** \
at the due date, labelled with its name.

Milestone windows
^^^^^^^^^^^^^^^^^

Use ``start`` and ``end`` when the duration of the milestone matters as well as its delivery date, for \
example a testing phase or a customer trial that has to happen within a set period:

.. code-block:: yaml

          - milestone: "M1"
            start: "2026-03-01"
            end: "2026-04-30"

On the project timeline a window is drawn as a **dotted red line at each end, joined by a line across the top**. \
In tables its dates are shown together, for example ``2026-03-01 to 2026-04-30``.

Windows can **overlap** each other. For example, customer trials can begin before beta testing has finished.

A window is **due on its end date**. Whenever the report needs a single date for a milestone, it uses the end: \
to check whether a workpackage finishes in time, to decide which milestone a task is needed for, and to decide \
which milestone is current.

Relative dates
--------------

Instead of a fixed date, ``date``, ``start`` and ``end`` can be written **relative to another milestone** of \
the same project. If that milestone moves, everything that depends on it moves too, so you only need to change \
one date.

A relative date is written as:

.. code-block:: text

    <milestone>.<date, start or end> + <number> <days, weeks, months or years>

For example:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Written as
     - Means
   * - ``"M1.date + 2 weeks"``
     - Two weeks after M1
   * - ``"M1.end + 1 day"``
     - The day after M1's window closes
   * - ``"M1.start - 10 days"``
     - Ten days before M1's window opens
   * - ``"M2.end + 6 months"``
     - Six months after M2 is due
   * - ``"M3.start"``
     - The same day M3 starts
   * - ``"start + 7 weeks"``
     - Seven weeks after **this** milestone's own start - an easy way to give a window a length

A full example, where moving M1 moves M2 and M3 with it:

.. code-block:: yaml

        milestones:
          - milestone: "M1"
            start: "2026-03-01"
            end: "2026-04-30"
          # Opens the day after M1 closes, and lasts seven weeks
          - milestone: "M2"
            start: "M1.end + 1 day"
            end: "start + 7 weeks"
          # Due three months after M2
          - milestone: "M3"
            date: "M2.end + 3 months"

Things to know about relative dates:

- **Use whole numbers.** ``1 day`` and ``2 days`` both work; ``1.5 weeks`` does not. Use ``+`` for later and \
  ``-`` for earlier.
- **Leaving out the milestone name** means "this milestone", as in ``"start + 7 weeks"``.
- **``date`` and ``end`` mean the same thing** when referring to another milestone: the day it is due. So \
  ``M1.end`` works whether M1 has a due date only or is a window.
- **``start`` of a milestone with only a due date** is simply its date.
- **Months and years follow the calendar.** One month after 15 January is 15 February. If the day does not \
  exist, the last day of the month is used, so one month after 31 January is 28 February (or 29th in a leap year).
- **Order does not matter.** A milestone can refer to one listed below it.
- **No loops.** A milestone cannot depend on itself, either directly or through others, for example M1 based on \
  M2 while M2 is based on M1.
- **Same project only.** A milestone can only refer to milestones listed in the same project.

Writing dates
-------------

Write fixed dates as ``YYYY-MM-DD``, for example ``"2026-03-31"``. Putting dates, including relative dates, \
in quotes is recommended but not required.

How milestones are used in the report
-------------------------------------

Project timeline
    Each project's milestones are drawn on its timeline: due dates as a dashed line, windows as a bracket \
    across the top. Today is also marked.

Passed, current and upcoming
    The **current** milestone of a project is the next one due: the first whose date (or end date, for a window) \
    is today or later. Milestones before it are marked **Passed**, and those after it **Upcoming**.

Workpackages
    A :doc:`workpackage <workpackages>` can name the milestone it is working towards. It must finish by that \
    milestone's due date, to the month, or it is marked ``OUTSIDE MILESTONE``.

Tasks
    On the project page each :doc:`task <tasks>` is counted against the milestone it is needed for: the first \
    milestone due on or after the task's forecast finish. A task with no ``start`` is assumed to start at the \
    latest milestone due on or before its first status update.

Milestone pages
    The milestones overview lists every milestone, which projects it is current for and when it is next due. Each \
    milestone has its own page listing every project that has dated it, with the start (for windows) and end dates.

A milestone that a project lists but that is not in the milestones file is not shown in the report, so check \
the names match exactly, including capitals.

Mistakes that are caught
------------------------

If a milestone cannot be understood, the report stops with a message starting ``ERROR :`` that names the \
milestone, the project and the problem, and no report is produced. Fix the input and run it again.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Problem
     - How to fix it
   * - Only a ``start``, or only an ``end``
     - A window needs both. If only the delivery date matters, use ``date`` instead
   * - A ``date`` together with a ``start`` or ``end``
     - Choose one: ``date`` for a due date only, or ``start`` and ``end`` for a window
   * - A window ends before it starts
     - Check the dates, or the ``+`` and ``-`` in relative dates
   * - A date that cannot be read
     - Write it as ``YYYY-MM-DD``, or as a relative date such as ``"M1.start + 6 months"``
   * - An unknown unit, such as ``fortnights``
     - Use ``days``, ``weeks``, ``months`` or ``years``
   * - A relative date refers to a milestone not in the project
     - Add that milestone to the project, or check the spelling of its name
   * - A milestone depends on itself
     - Give one of the milestones in the loop a fixed date
   * - The same milestone listed twice in a project
     - Remove one of them
   * - The same milestone name defined twice in the milestones file
     - Give each milestone a unique name
   * - An unexpected field, such as ``finish``
     - Check the spelling. The allowed fields are listed above

The ``examples/milestones/errors`` directory has a small example of each of these.

Examples
--------

The milestones of the ``simple`` example:

.. literalinclude:: ../../../examples/simple/milestones.yaml
    :language: yaml

The ``milestones/windows`` example shows milestones with a due date only, overlapping windows and relative dates \
together in one project. Its comments explain each one:

.. literalinclude:: ../../../examples/milestones/windows/projects.yaml
    :language: yaml

The timeline of that project. M0 and M4 have a due date only, and are drawn as dashed lines. M1, M2 and M3 \
are windows, drawn as a dotted line at each end joined across the top; M2 and M3 overlap. Today is also marked:

.. image:: /images/milestone_timeline.png
   :align: center
