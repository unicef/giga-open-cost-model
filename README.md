# Giga Models

## Setup

Use [poetry]() to create a local development environment.
Poetry is a tool for dependency management in Python, and you can install it with:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

To build the poetry environment, navigate to the root directory and run:

```bash
poetry install
```

## Tests

You can use poetry to run tests after the environment has been built:

```bash
poetry run pytest
```

## Repository Structure

The python library in this repository is organized as follows:
* `giga/compute`: contains generic computations used across multiple Giga models
* `giga/connect`: contains connectivity technology specific computations
* `giga/schemas`: contains the data definitions used by the Giga models
 