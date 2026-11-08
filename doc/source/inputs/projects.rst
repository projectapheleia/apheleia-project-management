.. _projects:

Projects
========

Overview
--------

Projects are the top level of the plan. Each project has a start and end date, and a list of the \
:doc:`milestones <milestones>` that apply to it, with the date each is due.

Fields
------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``project``
     - Yes
     - Name of the project
   * - ``start``
     - No
     - Project start date
   * - ``end``
     - No
     - Project end date
   * - ``description``
     - No
     - Description of the project
   * - ``milestones``
     - No
     - List of milestones for this project, see below

Milestones
----------

Each entry in ``milestones`` has:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``milestone``
     - Yes
     - Name of a milestone defined in a :doc:`milestones <milestones>` file
   * - ``date``
     - See below
     - Date the milestone is due on this project
   * - ``start``
     - See below
     - Date the milestone window opens
   * - ``end``
     - See below
     - Date the milestone window closes, i.e. the date the milestone is due

A milestone is given either a ``date`` or both a ``start`` and an ``end``, not a mixture.

A milestone with a ``date`` is marked on the project timeline with a single vertical line. A milestone with a \
``start`` and ``end`` is a window, and is drawn as a dotted vertical line at each end joined by a horizontal \
line. Windows may overlap each other. In tables the two dates are combined, e.g. ``2026-03-01 to 2026-04-30``. \
A window milestone is due on its ``end`` date: that is the date used to check workpackages, to assign tasks and \
to decide which milestone is current. See the ``milestones/windows`` example.

Relative dates
~~~~~~~~~~~~~~

``date``, ``start`` and ``end`` can be written relative to another milestone of the same project, as \
``<milestone>.<field> [+|- <number> <unit>]``, where the field is ``date``, ``start`` or ``end`` and the unit is \
``days``, ``weeks``, ``months`` or ``years``. Without a milestone the field is the milestone's own, so \
``end: "start + 6 months"`` is a window six months long. Milestones can refer to each other in any order, \
but not in a loop. The ``date`` and ``end`` of a milestone are both the date it is due, and the ``start`` of a \
single date milestone is its ``date``.

.. code-block:: yaml

    - milestone: "M2"
      start: "M1.end + 1 day"
      end: "start + 7 weeks"

Milestones are marked on the project timeline. A milestone that is not defined in a milestones file is not shown.

Example
-------

.. literalinclude:: ../../../examples/simple/projects.yaml
    :language: yaml

``Project Beta`` shows the minimum definition: a project only needs a name, and can be filled in as the plan develops.

The timeline of a project, with its milestones and today marked:

.. image:: /images/project_timeline.png
   :align: center
