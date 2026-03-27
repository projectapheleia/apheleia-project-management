# AVL-RAL- Apheleia Verification Library Register Abstraction Layer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)


AVL-RAL has been developed by experienced, industry professional verification engineers to provide a simple, \
extensible verification component integrating a Register Abstraction Layer (RAL) based on [systemdrl](https://systemrdl-compiler.readthedocs.io/en/stable/index.html/). \
developed in [Python](https://www.python.org/) and the [AVL](https://avl-core.readthedocs.io/en/latest/index.html) library.

AVL is built on the [CocoTB](https://docs.cocotb.org/en/stable/) framework.

## CocoTB 2.0

AVL-RAL supports CocoTB2.0 https://docs.cocotb.org/en/development/upgrade-2.0.html. This was introduced in v0.2.0.

## Component Features

---

## 📦 Installation

Unfortunately avl-ral isn't available on PyPi. As such to pip install you need to use the longer avl-register-abstraction-layer name. Once install avl_ral is the short-cut.

### Using `pip`
```sh
# Standard build
pip install avl-register-abstraction-layer

# Development build
pip install avl-register-abstraction-layer[dev]
```

### Install from Source
```sh
git clone https://github.com/projectapheleia/avl-ral.git
cd avl-ral

# Standard build
pip install .

# Development build
pip install .[dev]
```

Alternatively if you want to create a [virtual environment](https://docs.python.org/3/library/venv.html) rather than install globally a script is provided. This will install, with edit privileges to local virtual environment.

This script assumes you have [Graphviz](https://graphviz.org/download/) and appropriate simulator installed, so all examples and documentation will build out of the box.

```sh
git clone https://github.com/projectapheleia/avl-ral.git
cd avl-ral
source avl-ral.sh
```

## 📖 Documentation

In order to build the documentation you must have installed the development build.

### Build from Source
```sh
cd docs
make html
<browser> build/html/index.html
```
## 🏃 Examples

In order to run all the examples you must have installed the development build.

To run all examples:

```sh
cd examples

# To run
make -j 8 sim

# To clean
make -j 8 clean
```

To run an individual example:

```sh
cd examples/THE EXAMPLE YOU WANT

# To run
make sim

# To clean
make clean
```

The examples use the [CocoTB Makefile](https://docs.cocotb.org/en/stable/building.html) and default to [Verilator](https://www.veripool.org/verilator/) with all waveforms generated. This can be modified using the standard CocoTB build system.

---


## 🧹 Code Style & Linting

This project uses [**Ruff**](https://docs.astral.sh/ruff/) for linting and formatting.

Check code for issues:

```sh
ruff check .
```

Automatically fix common issues:

```sh
ruff check . --fix
```



## 📧 Contact

- Email: avl@projectapheleia.net
- GitHub: [projectapheleia](https://github.com/projectapheleia)
