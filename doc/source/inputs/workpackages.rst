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

Example
-------

.. literalinclude:: ../../../examples/simple/workpackages.yaml
    :language: yaml

The effort allocated to a project's workpackages, stacked by resource:

.. image:: /images/workpackage_allocations.png
   :align: center
