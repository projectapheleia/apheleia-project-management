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

Simple
------

``examples/simple``

A minimal semiconductor project. One fully defined project and one with only a name, three resources, \
three workpackages and three tasks, with one file for each type.

This is the best starting point for a new plan. The files are shown in full on each of the \
:doc:`input file <../inputs/inputs>` pages.

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
