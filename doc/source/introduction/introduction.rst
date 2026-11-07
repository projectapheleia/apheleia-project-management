Welcome to Apheleia Project Management's Documentation
======================================================

What is Apheleia Project Management?
------------------------------------

**Apheleia Project Management** is a lightweight project planning and tracking tool developed in \
`Python <https://www.python.org/downloads/>`_.

Projects, milestones, resources, workpackages and tasks are described in plain `YAML <https://yaml.org/>`_ files. \
A single command reads those files and generates a static, interactive HTML report containing timelines, \
resource allocations and task progress.

Why Use Apheleia Project Management?
------------------------------------

Most project management tools keep the plan in a database behind a web front end, or in a spreadsheet that \
only one person can edit at a time. Neither sits well alongside the engineering work it describes.

By keeping the plan in text files the plan can be stored in the same revision control system as the project itself. \
Changes can be reviewed, diffed and merged like any other source file, and the history of the plan comes for free.

Because the inputs are simply a directory of YAML files, the plan can be split however suits the team. A small \
project may keep everything in five files. A larger one may keep shared definitions in one place and let each \
engineer own a file containing the status of their own tasks.

The report is generated as static HTML. It needs no server, no database and no licence, and can be opened \
directly in a browser, archived alongside a release or published by a CI job.

What Does the Report Show?
--------------------------

.. image:: /images/report_overview.png
   :align: center

- Project timelines, with milestones and today's date marked
- Workpackage timelines and the effort allocated to each
- Resource availability, and how each resource is allocated across projects and workpackages
- Task timelines, progress and forecast completion dates based on effort spent and remaining

All charts are interactive, built using `plotly <https://plotly.com/python/>`_, and can be viewed at \
monthly, quarterly or yearly scale. Clicking a bar or segment navigates to the page for that item.

Who is Apheleia Project Management Aimed At?
--------------------------------------------

Apheleia Project Management is aimed at engineering teams and project leads who want a clear view of who is \
working on what, and when, without adopting a heavyweight tool.

Nothing in the tool is specific to any one industry. The examples include both a chip development \
and a construction project.
