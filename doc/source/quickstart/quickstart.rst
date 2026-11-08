Quickstart Guide
================

This guide will help you get started with Apheleia Project Management. It will show you how to install the tool, \
build the examples, and how to create a report for your own projects.

Before you start this guide, you should have a basic understanding of Python and `YAML <https://yaml.org/>`_.

In order to run the examples you will need to have installed:

- `Python <https://www.python.org/downloads/>`_ 3.10 or later

- A web browser to view the generated report

In order to build the documentation you will also need:

- `Graphviz <https://graphviz.org/download/>`_

Installing From PyPI
--------------------

Apheleia Project Management is available on `PyPI <https://pypi.org/project/apheleia-project-management/>`_.

.. code-block:: bash

    pip install apheleia-project-management

Installing From Source
----------------------

Apheleia Project Management is available via `GitHub <https://github.com/projectapheleia/apheleia-project-management.git>`_.

All required libraries are included in the pyproject.toml file.

.. code-block:: bash

    git clone https://github.com/projectapheleia/apheleia-project-management.git
    cd apheleia-project-management

    # Standard build
    pip install .

    # Development build
    pip install .[dev]

Or if you plan on editing the source code, you can install in editable mode:

.. code-block:: bash

    git clone https://github.com/projectapheleia/apheleia-project-management.git
    cd apheleia-project-management
    pip install --editable .[dev]

A script is provided to setup a python virtual environment and install all dependencies for development.

.. code-block:: bash

    git clone https://github.com/projectapheleia/apheleia-project-management.git
    cd apheleia-project-management
    source setup.sh

This assumes you have `Graphviz <https://graphviz.org/download/>`_ installed, to ensure the documentation can be built out of the box.

Building The Docs
-----------------

.. code-block:: bash

    cd doc
    make html
    <browser> build/html/index.html

The API module pages are generated from the source. If modules are added or removed, regenerate them from \
the root of the repository before building:

.. code-block:: bash

    python3 doc/gen_all_rst.py

Running the Examples
--------------------

The examples are located in the examples directory.

To build the report for all examples:

.. code-block:: bash

    cd examples
    make report

To clean up the examples:

.. code-block:: bash

    cd examples
    make clean

Alternatively, you can build each example individually:

.. code-block:: bash

    cd examples/simple
    make report
    <browser> html/index.html

Creating Your Own Report
------------------------

1. Create a directory to hold your plan.

2. Add YAML files describing your :doc:`milestones <../inputs/milestones>`, :doc:`resources <../inputs/resources>`, \
   :doc:`projects <../inputs/projects>`, :doc:`workpackages <../inputs/workpackages>` and :doc:`tasks <../inputs/tasks>`. \
   The :doc:`simple example <../examples/examples>` is a good starting point.

3. Generate the report:

.. code-block:: bash

    apheleia_project_report --input <plan directory> --html <output directory>
