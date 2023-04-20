# Giga Models

You can find a reference glossary that provides in-depth explanations below.

## Glossary

* [Local Environment Setup](#setup)
* [Library Architecture](docs/arch.md)
* [Model Documentation](docs/models.md)
* [Notebooks Overview](notebooks/README.md)
* [Application Deployment](#deployment)
* [Command Line Interfaces](#cli)

## Setup

Note: this repositroy uses git lfs for some of the larger files.
Please install [git lfs](https://git-lfs.com/), and then run `git lfs pull` to fetch copies of the larger files locally.
Use [poetry](https://python-poetry.org/) to create a local development environment.
Poetry is a tool for dependency management in Python.
You can use the helper `dev` CLI to build the environment locally:

```bash
./dev build
```

To start a local notebook server simply run:

```bash
./dev start-notebook
```

You can use the `dev` CLI to also run pytest tests:

```bash
./dev test
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

Each of the connectivity models is briefly described below.
For more details please see [here](docs/models.md).
The cost models are the following:

* **Fiber Model**: asses the costs of connectivity using fiber. Can optionally consider economies of scale, which allows schools that already connected with fiber during modeling to be used as fiber nodes. CapEx considers infrastructure costs of laying fiber, modem/terminal installation costs at school and solar installation if needed. OpEx considers maintenance of fiber infrastructure, maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **Cellular Model**: asses the costs of connectivity using cellular. CapEx considers modem installation at school and solar installation if needed. No other infrastructure costs are considered. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **P2P Model**: asses the cost of connectivity using point to point wireless technology. CapEx considers infrastructure costs of installing a transmitted at a cell tower, modem/terminal installation costs at school and solar installation if needed. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **Satellite Model**: asses the cost of connectivity using LEO satellite. CapEx considers terminal installation at school and solar installation if needed. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.

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

## Adding a New Country

The library provides a number of helpers to add new countries that can be supported in the models.
There are a few steps that need to be completed in order to do this. 

1. Determine the default cost drivers for the country, and the code for the country that can be used with Project Connect APIs. Create a json file that has these parameters, see [here](conf/countries/rwanda.json) for an example of how to structure this file.
2. To drive the models, you need additional data for this country: electricity (optional), fiber node data, cellular tower data. You can find the format for these in the sub-sections below. Aggregate the data that you will need and place it in the workspace for this country.
3. You can add a new country by using the CLI as follows:  `./run add-new-country <your-country-parameters.json> <path-to-country-workspace> <PROJECT_CONNECT_API_TOKEN>`. This will register the country and make it available to the library models, fetch the most up to date school data for that country, merge that data with any existing workspace data like electricity data, and create a cache for schools and infrastructure data
4. Synchronize the new country data with remote storage, the current CLI is setup to work with an object store called Google Cloud Store, where all the workspace blobs/artifacts are persisted and updated using `./run upload-workspace <path-to-country-workspace>`
5. You are all set! After the updated version of the application has been re-deployed, the new country will be available to run models against 

Note that step 3 above combines multiple commands into a single executable for simplicity.
If you want to run each of these commands separately see the [Appendix](#appendix) for more information.

For more information on how you can use the `run` CLI, see the descriptions below (to generate the help text, execute `./run` from command line without any input arguments, see [here](run#L53) for the description):

```
  upload-workspace <workspace-dir> 				Copies the data workspace from the specified target directory to a storage bucket
  fetch-workspace <workspace-dir> 				Copies the data workspace from a storage bucket to the specified target directory
  register-country <parameter-file> 				Registers a new country in the modeling library
  fetch-school-data <workspace> <api-key> <country> 		Pulls up to date school data from Project Connect APIs
  create-cache <workspace> 					Creates a cache of pairwise distances that can be used by the models
  add-new-country <parameter-file> <workspace> <api-key> 	Registers country, pulls school data, creates cache
  remove-country <parameter-file> 				Removes a country from the modeling library
```

### Electricity Data

Electricity data is currently not available through Project Connect APIs, and is thus managed independently.
If you know the electricity status of the schools in your country of interest, you can populate the workspace with a .csv table that contains entries of the following form:

| Field         | Type          | Description                   |
| ------------- | ------------- | ----------------------------- |
| giga_id_school | str           | Unique school identifier |
| has_electricity    | bool   | Whether the school has electricity   |

If no electricity data is provided all schools will be assumed to not have electricity.

---

### Fiber Node Data

Fiber nodes for a country can be specified as unique coordinates using the schema below in a csv table of the countries' workspace:


| Field         | Type          | Description                   |
| ------------- | ------------- | ----------------------------- |
| coordinate_id | str           | Unique coordinate identifier |
| coordinate    | LatLonPoint   | Latitude and longitude point  |
| properties    | json (optional) | Additional properties         |

---

### Cell Tower Data

Cell tower data for a country can be specified using the schema below in a csv table of the countries' workspace:

| Field        | Type                     | Description                      |
| ------------ | ------------------------ | -------------------------------- |
| tower_id     | str                      | Unique tower identifier          |
| operator     | str                      | Cellular tower operator          |
| outdoor      | bool                     | Whether the tower is outdoor     |
| lat          | float                    | Latitude of the tower            |
| lon          | float                    | Longitude of the tower           |
| height       | float                    | Height of the tower              |
| technologies | List[CellTechnology]     | List of supported technologies [2G, 3G, 4G, LTE] |

---


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

### GCP and Auth0 Configurations

Configuring the deployment is done in two places, the `stack` CLI and the deployment manifest of helm values.
Most of the GCP specific deployment parameters are defined in the stack CLI, the ones of interest are the following:

* The container registry, which is where all the built docker containers are pushed to and pulled from, see [here](stack#L6)
* The cluster name, which points to the k8s cluster running the deployment, see [here](stack#L12)
* The auth configuration is managed entirely inside of our deployment manifest, see [here](deployment/helm/prod.yaml#L31)

Migrating to a different cloud provider or a different auth system would require updating these parameters.

## CLI

The library exposes the following CLI, each with a different purpose.

For local development, the `./dev` CLI can be used with the following sub-commands:

```
  build					Builds the modeling environment locally
  start-notebook		        Start a jupyterlab notebook server locally
  test					Runs the unit test suite
  lint					Runs a flake8 lint check against PEP 8
  format				Modifies non PEP 8 compliant code to be style compliant
  clean-notebook <notebook-path> 	Removes rendered html from jupyter notebooks
```

For managing deployments, the `./stack` CLI can be used with the following sub-commands:

```
  up 						        Deploys the notebook stack to a k8s cluster
  down 						        Tears down the notebook stack
  install 					        Install minikube, helm, etc.
  auth 						        Authenticate with GCP
  create-image 					        Builds docker image for off-platform models
  push-image 					        Pushes model docker image to a remote registry
  start-container <workspace-dir> 	                Launches a Docker container and mounts a workspace directory to it
  launch  					        Launches jupyterhub on a kubernetes cluster using helm
  stop  					        Stops the jupyterhub deployment
  reset-password  <user-email> 		                Sends a password reset email for notebook user
```

For running the models and relevant data pipelines, the `./run` CLI can be used with the following sub-commands:

```
  upload-workspace <workspace-dir> 			Copies the data workspace from the specified target directory to a storage bucket
  fetch-workspace <workspace-dir> 			Copies the data workspace from a storage bucket to the specified target directory
```

## Appendix

The individual steps for registering a new country can be found below.
These steps are combined in the command: `./run add-new-country <your-country-parameters.json> <path-to-country-workspace> <PROJECT_CONNECT_API_TOKEN>`.

1. Register the country using the CLI: `./run register-country <your-country-parameters.json>`
2. Now the country is registered and will be available to the models. However, to drive the models, you need additional data for this country: electricity (optional), fiber node data, cellular tower data. You can find the format for these in the sub-sections below. Aggregate the data that you will need and place it in the workspace for this country.
3. Generate the most up to date school dataset for this country by using the CLI: `./run fetch-school-data <path-to-country-workspace> <PROJECT_CONNECT_API_TOKEN> <country-name>`
4. [OPTIONAL] If you would like, create a cache for the schools and infrastructure data that can be used to improve compute times in the models by using the CLI: `./run create-cache <path-to-country-workspace>`