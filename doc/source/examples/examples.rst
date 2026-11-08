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

Resources
---------

``examples/resources``

``availability`` shows a mix of resources: some active today at full time, part time or on leave at 0%, and \
some with no active period because they have left, have not yet started or are between periods. Their \
availabilities range from 0 to 100%. It also has periods given out of order, an availability written as \
``25%``, a single period given without ``periods`` and a resource with no dates at all.

``errors`` has one directory for each way a resource's availability periods can be invalid: periods that \
overlap, an end before the start, an availability outside 0 to 100, a period with no end that is not the last, \
periods mixed with a top level start, an empty list of periods, unexpected fields and dates that cannot be read. \
``make report`` in ``errors`` checks each fails in the same way as the milestone error cases.

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
