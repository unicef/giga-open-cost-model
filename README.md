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
* `giga/data`: utilities for data managment including aggregating data from external data sources and APIs
* `giga/schemas`: contains the data definitions used by the Giga models
* `giga/utils`: various helper tools
* `giga/viz`: plotting helpers

## School Data

To generate a school dataset for a given country, we can use the API client in the library that can fetch school data from the project connect API - spec can be found [here](https://uni-connect-services-dev.azurewebsites.net/api/v1/#/School/get_api_v1_schools_country__country_id_).
The client can fetch school data by specified country, currently `Brazil` and `Rwanda` are supported.
The number of schools in a given country isn't available through the API and has be determined dynamically.
The default request parameters should fetch all the schools for the two countries above in a single request.

```python
client = GigaAPIClient(token) # auth token provisioned by Giga

country = 'Brazil'
schools = client.get_schools(country) # ~141,000 schools available for Brazil
```

To create a table of the schools after they've been fetched from the project connect API:
```python
from giga.schemas.school import GigaSchoolTable

table = GigaSchoolTable(schools=schools)

# to reduce the data to a table of just lat/lon coordinates
coordinate_table = table.to_coordinates()
```

## Lint

To run a `flake8` lint check that checks against the PEP 8 standard you can:

```bash
./dev lint
```

To autoformat code that is non PEP 8 compliant run:

```bash
./dev format
```
