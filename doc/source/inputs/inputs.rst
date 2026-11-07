.. _inputs:

Input Files
===========

Overview
--------

All inputs to Apheleia Project Management are `YAML <https://yaml.org/>`_ files. Each file has two top level keys:

- ``type`` - what the file defines
- ``data`` - a list of definitions of that type

.. code-block:: yaml

    type: "milestones_definitions"
    data:
      - milestone: "M0"
        description: "Project Definition"

Five types are supported:

.. list-table::
   :header-rows: 1

   * - Type
     - Defines
   * - ``milestones_definitions``
     - :doc:`milestones`
   * - ``resources_definitions``
     - :doc:`resources`
   * - ``projects_definitions``
     - :doc:`projects`
   * - ``workpackages_definitions``
     - :doc:`workpackages`
   * - ``tasks_definitions``
     - :doc:`tasks`

File Discovery
--------------

The input directory is searched recursively for files with the ``.yaml`` extension. Files that are empty, \
or have no ``type`` key, are ignored, so the plan can sit alongside other YAML files without conflict.

File names and directory structure are not significant. All definitions of the same type are combined, \
regardless of which file they were found in. This means a plan can be:

- A single file per type, as in the ``simple`` and ``construction_single`` examples
- Split by owner, for example shared definitions in one directory and a ``tasks.yaml`` per engineer, \
  as in the ``construction_multi`` example

Splitting by owner keeps merge conflicts to a minimum when several people update their status at the same time.

Names
-----

Every milestone, resource, project, workpackage and task is identified by its name. Names are used to link \
definitions together, for example a task names the project, workpackage and resource it belongs to. \
Names must therefore match exactly, including case and spaces.

Names must be unique within their type. Defining the same name twice, even in different files, is an error.

Each name is also used to create the file name of its page in the report, by converting it to lower case \
and replacing spaces with underscores.

Dates
-----

Any string value that looks like a date is converted to a date. Dates are best written in ``YYYY-MM-DD`` format \
and quoted, so that YAML does not interpret them itself:

.. code-block:: yaml

    start: "2026-01-14"

A month may be given as ``YYYY-MM``, which is taken as the first day of that month. This is convenient for \
:doc:`workpackage allocations <workpackages>`.

The values ``""``, ``None``, ``null`` and ``nan`` (in any case) are treated as empty, so an open-ended \
date can be written as:

.. code-block:: yaml

    end: None

Strings of the form ``M<number>``, for example ``M10``, are never converted to dates, so that they can be \
used as milestone names.
