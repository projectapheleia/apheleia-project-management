.. _examples:

Examples
========

Overview
--------

The examples are located in the examples directory. Each example is a directory of :doc:`input files <../inputs/inputs>` \
and a ``Makefile`` to build its report.

To build the report for all examples:

.. code-block:: bash

    cd examples
    make report

To build an individual example:

.. code-block:: bash

    cd examples/simple
    make report
    <browser> html/index.html

To clean up:

.. code-block:: bash

    make clean

Every example ``Makefile`` gives the report date with ``--today 2026-11-09`` (the ``TODAY`` variable), so each \
report is the same whatever day it is built. See :doc:`../report/report`. To build one for another date, or with \
no date, set ``TODAY``:

.. code-block:: bash

    make report TODAY=2027-01-04
    make report TODAY=None

Simple
------

``examples/simple``

A minimal semiconductor project. One fully defined project and one with only a name, three resources, \
three workpackages and three tasks, with one file for each type. The resources show periods of leave, part time \
availability and a single open ended period.

This is the best starting point for a new plan. The files are shown in full on each of the \
:doc:`input file <../inputs/inputs>` pages.

Milestones
----------

``examples/milestones``

Examples of project milestones, with the bare minimum around them: no resources, workpackages or tasks.

``windows`` shows single date milestones, drawn as a vertical line, overlapping milestones with a start and \
end date, drawn as a window, and dates relative to other milestones.

``errors`` has one directory for each way a milestone can be invalid: a date mixed with a start or end, only a \
start or an end, an end before the start, unexpected fields, duplicate milestones, dates that cannot be read, \
and relative dates that refer to an unknown milestone or to themselves. ``make report`` in ``errors`` runs the \
report on each and passes only if the report fails with a non-zero exit status and the expected ``ERROR :`` \
message, and does not generate a report.

Workpackages
------------

``examples/workpackages``

``estimates`` shows workpackages allocated the same effort (6 person-months) with no estimate, a generous estimate \
of 1 man-year, a low estimate of 60 man-days (so it is flagged ``OVER ESTIMATE``) and an estimate equal to the \
allocation.

``task_effort`` checks the tasks of each workpackage against it: tasks that fit, tasks that now need more effort \
than is allocated (``TASKS OVER ALLOCATION``), task estimates that add up to more than the workpackage estimate \
(``TASKS OVER ESTIMATE``), a task with no estimate, and a workpackage with no tasks.

``errors`` has one directory for each way an estimate can be invalid: an unknown unit, no unit, a bare number, \
something that is not a number, a negative estimate and zero. ``make report`` in ``errors`` checks each fails in \
the same way as the milestone error cases.

Tasks
-----

``examples/tasks``

``estimates`` shows good estimates (on track, finished early, finished exactly on the estimate) and bad ones: \
remaining effort that takes a task past its estimate, effort already spent past it, a task finished over it, \
work that grows at every status update, a task over its estimate before it has started, and a task with no \
estimate. The over estimate tasks are listed on the project summary, the tasks page and the workpackage and \
resource pages.

``shared`` has tasks shared by two and three people, written as a list of names, beside tasks done by one \
person. Each shared task is shown on the page of everyone working on it.

``units`` gives task effort in man-days, man-weeks, man-months and man-years, mixing units within a task. \
``default_unit`` sets ``task_unit`` to man-weeks, so plain numbers are man-weeks, alongside values with a unit \
of their own.

``stale`` sets ``stale_days`` to 30 and has a complete task, which is never stale, tasks not updated for months, \
which are ``STALE``, and a task updated recently. Being stale depends on the report date, which the \
``Makefile`` sets to 2026-11-09 with ``--today``; on a later date the recent task becomes stale too. ``stale_off`` is the same plan with ``stale_days: null``, which \
turns the check off.

``errors`` has one directory for each way a task can be invalid: an estimate with an unknown unit, that is not a \
number, zero or negative; status effort in an unknown unit or negative; a status update with no remaining, an \
invalid date or the same date as another; a unit given as a field; no status updates; an empty list of resources, \
a resource listed twice and a misspelt resource; an unknown ``task_unit``; and a ``stale_days`` that is text \
or zero. ``make report`` in ``errors`` \
checks each fails in the same way as the milestone error cases.

Resources
---------

``examples/resources``

``availability`` shows a mix of resources: some active today at full time, part time or on leave at 0%, and \
some with no active period because they have left, have not yet started or are between periods. Their \
availabilities range from 0 to 100%. It also has periods given out of order, an availability written as \
``25%``, a single period given without ``periods`` and a resource with no dates at all.

``over_allocation`` has a resource shared by two projects that together allocate 120% of their time, a part \
time resource allocated exactly their hours, a resource allocated full time in a month with two weeks of leave, \
and one allocated before they join. They are shown on the *Allocation* tab of the resources overview.

``errors`` has one directory for each way a resource's availability periods can be invalid: periods that \
overlap, an end before the start, an availability outside 0 to 100, a period with no end that is not the last, \
periods mixed with a top level start, an empty list of periods, unexpected fields and dates that cannot be read. \
``make report`` in ``errors`` checks each fails in the same way as the milestone error cases.

Format
------

``examples/format``

Two reports of the same plan, with a format and themes of their own. See :doc:`../report/format`.

``eighties`` is neon and geometric. It changes the title and logo and adds two themes to the built-in ones.

``noir`` is black and white, with a silhouette logo. It replaces the built-in themes with ``Noir Light`` and ``Noir Dark``.

``errors`` has one directory for each way the format can be invalid: unexpected fields, a default theme or an \
extended theme that does not exist, themes that extend each other, a theme defined twice, a missing logo file, a logo \
given as a file and as SVG, values that would break the style sheet, a bars setting that is not understood and \
no themes to offer. ``make report`` in ``errors`` checks each fails in the same way as the milestone error cases.

Report Date
-----------

``examples/today``

``none`` is the ``simple`` example with no report date (``--today None``). Nothing is marked as today, forecasts \
start from each task's latest status update, and stale tasks, the current milestone and availability are checked \
against the latest status update in the input. ``errors`` has a report date that is not a date, which is rejected.

Construction Single
-------------------

``examples/construction_single``

A larger, multi-year construction project, again with one file for each type. It shows how the same tool \
applies outside of engineering, and how the report scales with a more realistic number of resources, \
workpackages and tasks.

Construction Multi
------------------

``examples/construction_multi``

The same project as ``construction_single``, with the plan split by owner:

.. code-block:: text

    construction_multi
    ├── Makefile
    ├── shared
    │   ├── milestones.yaml
    │   ├── projects.yaml
    │   ├── resources.yaml
    │   └── workpackages.yaml
    └── resources
        ├── akhan
        │   └── tasks.yaml
        ├── bfoster
        │   └── tasks.yaml
        └── ...

The shared definitions are maintained by the project lead. Each resource has their own directory containing \
only their tasks, so they can update their own status without editing a file anyone else is working on.

Because the input directory is searched recursively and all definitions of the same type are combined, \
no configuration is needed to support this layout.

.. literalinclude:: ../../../examples/construction_multi/resources/akhan/tasks.yaml
    :language: yaml
