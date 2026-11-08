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

``milestones`` lists the :doc:`milestones <milestones>` that apply to the project and gives each one its dates. \
Each entry has:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - What it means
   * - ``milestone``
     - Yes
     - The name of a milestone from a :doc:`milestones <milestones>` file
   * - ``date``
     - See below
     - The date the milestone is due, when only the delivery date matters
   * - ``start``
     - See below
     - The day a milestone window opens
   * - ``end``
     - See below
     - The day a milestone window closes, which is the day it is due

Give each milestone **either** a ``date`` **or** both a ``start`` and an ``end``. Any of these can be a fixed \
date such as ``"2026-03-31"`` or relative to another milestone of the project, such as ``"M1.end + 6 weeks"``.

.. code-block:: yaml

        milestones:
          - milestone: "M1"
            date: "2026-02-01"
          - milestone: "M2"
            start: "M1.date + 1 day"
            end: "start + 7 weeks"

See :doc:`milestones` for milestones with a due date, windows, relative dates, how milestones appear in the report \
and the mistakes that are caught.

Example
-------

.. literalinclude:: ../../../examples/simple/projects.yaml
    :language: yaml

``Project Beta`` shows the minimum definition: a project only needs a name, and can be filled in as the plan develops.

The timeline of a project, with its milestones and today marked:

.. image:: /images/project_timeline.png
   :align: center
