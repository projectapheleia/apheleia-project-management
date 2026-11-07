.. _resources:

Resources
=========

Overview
--------

Resources are the people available to work on projects. Each resource has a period over which they are \
available, which is used to show how many people can be called on over time.

Fields
------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``resource``
     - Yes
     - Name of the resource
   * - ``uname``
     - No
     - User name, for example a login or email alias
   * - ``start``
     - No
     - Date the resource becomes available
   * - ``end``
     - No
     - Date the resource stops being available. If empty the resource is assumed to be available \
       until the end of the charts
   * - ``profile``
     - No
     - Link to a profile page for the resource

No other fields are permitted.

The ``resource`` name is used by :doc:`workpackage allocations <workpackages>` and :doc:`tasks <tasks>`.

Example
-------

.. literalinclude:: ../../../examples/simple/resources.yaml
    :language: yaml

The availability of each resource:

.. image:: /images/resource_availability.png
   :align: center
