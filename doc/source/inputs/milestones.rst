.. _milestones:

Milestones
==========

Overview
--------

Milestones are the named checkpoints shared by all projects, for example *Architectural Proposal* or \
*Tape-out*. They are defined once and then given a date by each :doc:`project <projects>` that uses them.

Defining the milestones separately to their dates allows the same set of milestones to be used across many \
projects, so that projects can be compared like for like.

Fields
------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``milestone``
     - Yes
     - Name of the milestone
   * - ``description``
     - No
     - Description of the milestone

No other fields are permitted. In particular a milestone has no date of its own - dates are given by each project.

Example
-------

.. literalinclude:: ../../../examples/simple/milestones.yaml
    :language: yaml
