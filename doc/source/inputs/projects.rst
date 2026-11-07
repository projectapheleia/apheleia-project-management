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
     - Yes
     - Date the milestone is due on this project

Milestones are marked on the project timeline. A milestone that is not defined in a milestones file is not shown.

Example
-------

.. literalinclude:: ../../../examples/simple/projects.yaml
    :language: yaml

``Project Beta`` shows the minimum definition: a project only needs a name, and can be filled in as the plan develops.

The timeline of a project, with its milestones and today marked:

.. image:: /images/project_timeline.png
   :align: center
