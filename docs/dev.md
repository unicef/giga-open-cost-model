
# Giga Dev Documentation

This documentation provides technical details on the Giga model's implementation,
setup, and deployment process.

Jump to:
* [Setup](#setup)
* [Deployment](#deployment)
* [CLI](#cli)

> Also see the following additional documentation:
> * [User overview](../README.md) and details on running each notebook.
> * [Model overview](models.md), including a breakdown of each model.
> * [Model data](data.md), including data schemas and how to update countries.
> * [Model architecture](arch.md), focusing on key parts of the library used for configuration, data aggregation, and model execution.
> * [Python documentation](../notebooks/dev/documentation.ipynb) automatically generated from the model source code.

### Repository Structure

The python library in this repository is organized into the following key categories to help manage the models and their parameters:

1. Models: the key building blocks of all computations performed by this library
2. Schemas: the definitions of all the model inputs and outputs, data requirements, and configurations
3. Data: the tooling to pull in and transform any external data into formats usable by the library
4. Utilities: helpers for connecting to APIs, visualizing outputs, and constructing inspect able and interactive interfaces
5. App: the application runner for configuring and starting the modeling application

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

### Lint

You can format local code using the following commands:

```bash
./dev lint    # Runs flake8 link check against PEP8 standard
./dev format  # Auto-formats code that is non PEP8-compliant
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

#### (Optional) Execute scenarios directly with Python

You can use the script below to run the total cost scenario by doing the following:

```bash
./total_cost_scenario.py --workspace <path-to-data-workspace>
					     --output-file <desired-output-file> # e.g. costs.csv
					     --scenario-type minimum-cost # minimum-cost, fiber, cellular, p2p, or satellite
```

The script above will use the school, fiber, and cellular data in the workspace specified, to create an output .csv table that contains cost information for each school in the input data set.
Additionally, you can specify the scenario type by choosing between a `minimum-cost` scenario or a single technology cost scenario (`fiber`, `cellular`, `p2p`, `satellite`).