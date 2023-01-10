# Giga Models

You can find a reference glossary that provides in-depth explanations below.

## Glossary

* [Local Environment Setup](#setup)
* [Library Architecture](docs/arch.md)
* [Model Documentation](docs/models.md)
* [Notebooks Overview](notebooks/README.md)
* [Application Deployment](#deployment)

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

The python library in this repository is organized into the following key categories to help manage the models and their parameters:

1. Models: the key building blocks of all computations performed by this library
2. Schemas: the definitions of all the model inputs and outputs, data requirements, and configurations
3. Data: the tooling to pull in and transform any external data into formats usable by the library
4. Utilities: helpers for connecting to APIs, visualizing outputs, and constructing inspect able and interactive interfaces
5. App: the application runner for configuring and starting the modeling application

### Models

All modeling capabilities are defined within `giga/models`. The models are further broken down into the following categories:

* Nodes: atomic, modular building blocks that contain a computation, transformation, or external data
* Components: stacks nodes together with a clear and specific purpose (e.g. use case driven - compute cost of fiber connection) prepares the models to join into the entities that solve a specific problem
* Scenarios: drives the computation by piecing together multiple components and solving a specific problem by deriving a key result. Allows same components to serve multiple purposes: e.g. answer the questions of what is the cost of connecting all schools in Rwanda to the internet? VS If there is a budget of $10M which schools should be connected to maximize the number of students with internet access?

### Architectural Overview

The architecture of the modeling library can be found [here](docs/arch.md).
It describes the key parts of the library - namely those used for configuration, data aggregation, and modeling execution.

### Data

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

## Deployment

To build the model container and re-deploy the notebook cluster simply run:

```bash
./stack up
```

To stop the cluster and clear resources run:

```bash
./stack down
```

Please note, you will need to have authenticated with GCP CLI and have k8s context referencing the right GKE cluster. 
For more details on this see below. 

### Cluster Details

Notebooks are deployed as a standalone application using [JupyterHub](https://jupyter.org/hub).
These notebooks allow users to interact with the giga models through an interactive dashboard and to visualize/plot the model outputs through a streamlined interfaces.

[Helm](https://helm.sh/) is used to manage the deployment - find the existing jupyterhub helm chart [here](https://artifacthub.io/packages/helm/jupyterhub/jupyterhub).
The deployment configuration for this chart can be found in `deployment/values/prod.yaml`.
The following configurations are managed with a custom configuration:
1. The base notebook container used in the deployment that includes the models
2. The authentication mechanism for users to access jupyterhub - auth0 is currently used


### Deployment Workflow
Please note that the workflow is currently manually managed with the CLI explained below.
The full deployment workflow looks as follows, which can all be managed with the `stack` CLI: 
1. Authenticate with GCP by running `./stack auth`. This will also configure the credentials for the GKE cluster to which jupyterhub is deployed
2. Create a Docker image for the models, you can use the CLI in the root dir: `./stack create-image`
3. Push the image to Actual's docker registry: `./stack push-image`
4. Update or launch a new instance of the cluster with `./stack launch` 

### Updating the Cluster + Local Testing

You can stop the jupyterhub cluster by running `./stack stop`.
If you need to update the single user image, you can rebuild it using the CLI above.
You can interact with the single user container locally by running `./stack start-container <local-workspace>`.
