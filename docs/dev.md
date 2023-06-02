
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

### Resource Requirements

The model application is typically memory constrained rather than CPU constrained.
The recommended minimum memory for a single model pod in k8s is 3 GB with a limit 5 GB.
The current configuration is set to reflect this as follows (from deployment/help/prod.yaml):

```
singleuser:
  # other configs ...
  cpu:
    limit:
    guarantee:
  memory:
    limit: 5G
    guarantee: 3G
```

Do note that no cpu limit is not set above.
Additionally, the somewhat large memory guarantee is needed to run models for all schools in large countries (like Brazil).
If the school data is broken down into smaller sub-regions for those larger countries, it's likely possible to make the memory guarantee significantly smaller.


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

### Authentication and Authorization Configuration

You can configure the application cluster to use a number of different authenticators, these include:

* github
* Azure Active Directory
* Auth0
* Google auth

You can read more about configuring each of these [here](https://z2jh.jupyter.org/en/stable/administrator/authentication.html).

To configure an authenticator you will need to update the helm values in deployment/help/prod.yaml under

```
hub:
  config:
    # authenticator configuration here, for auth0 see example below
    Auth0OAuthenticator:
      client_id: client-id-from-auth0-here
      client_secret: client-secret-from-auth0-here
      oauth_callback_url: https://your-jupyterhub-domain/hub/oauth_callback
      scope:
        - openid
        - email
      auth0_subdomain: prod-8ua-1yy9
    Authenticator:
      admin_users:
        - devops@example.com
      auto_login: true
    JupyterHub:
      authenticator_class: auth0
```

### GCP and Auth0 Configurations

Configuring the deployment is done in two places, the `stack` CLI and the deployment manifest of helm values.
Most of the GCP specific deployment parameters are defined in the stack CLI, the ones of interest are the following:

* The container registry, which is where all the built docker containers are pushed to and pulled from, see [here](stack#L6)
* The cluster name, which points to the k8s cluster running the deployment, see [here](stack#L12)
* The auth configuration is managed entirely inside of our deployment manifest, see [here](deployment/helm/prod.yaml#L31)

Migrating to a different cloud provider or a different auth system would require updating these parameters.

### Managing Voila Dashboards

Once the application is deployed you can create a standalone voila dashboard on a stand-alone url.
Currently, dashboard can not be shared between different accounts.
One way to have demo-able and sharable dashboards is to create a guest credential, create a dashboard for the application user associated with that credential, and sharing that credential and url with the user who needs access to the dashboard.
The standalone dashboard can support multi-tenantcy (e.g. multiple accounts logged in at the same time).
However, the dashboard is running in a single pod that is constrained by the deployed resources associated with a single-user pod.

To create a dashboard follow the steps below:
1. Log-in using the credential you want to provide dashboard access for (this could be your own personal account, a guest credential, or something else)
2. Navigate to the hub control panel - click `File` (top right) and `Hub Control Panel` (at the bottom of the menu)
3. Click on the `Dashboards` sub-menu at the top
4. Click `New Dashboard` to begin creating a new dashboard
5. Fill in the information for the dashboard you want to create by specifying the dashboard name (which will be reflected in the url), the description of the dashboard which will appear when the dashboard is first started, the framework - choose voila, and the relative path to the notebook that will be turned into a dashboard (see below for an example models dashboard)
6. Click `Save` which will create a container in which the dashboard runs

**Please note**: that on new deployments or releases the dashboard container will be stopped, and the dashboard will need to be recreated by following the steps above.

The properties of a dashboard (step 5) above are as follows:
* `Dashboard name` refers to the name of the dashboard and constructs the url under which the dashboard can be accessed. For example, if you call the dashboard `models`, then the user under which the dashboard was created can access the dashboard directly under https://<base-url>/hub/dashboards/models, for a given base url, the dashboard could be accessed directly by at https://giga.notebooks.actualhq.com/hub/dashboards/
* `Description` will be the brief text that shows up when the dashboard is starting. If anyone is accessing the dashboard through the url above directly, this property is not surfaced
* `Frameworks` specifies the dashboarding framework to use, for this application select `voila`
* `Relative Path` refers to the notebook in the single user container that will be used to create the dashboard. The primary notebook for this application can be found under `notebooks/cost-scenario.ipynb`

You can create a number of dashboard using different notebooks by following the steps above.

### Known Issues

#### SSL Certs

If you are spinning up a Jupyterhub cluster with a new SSL certificate (e.g. proxy.https.enabled set to true), you may run into a race condition when deploying to GKE clusters.
The race condition will results in the `autohttps` pods in the cluster producing timeout logs and you will not be able to access the https instance of the deployment.
You should be able to resolve this by re-configuring the autohttps deployment to sleep prior to starting up.
To do so:

```bash
kubectl edit deploy autohttps
```

```
       # ...
       containers:
       - image: traefik:v2.6.1
+        command: ["sh", "-c", "sleep 10 && /entrypoint.sh traefik"] # add this line
         imagePullPolicy: IfNotPresent
         # ...
```
This will trigger the deployment to restart and should resolve the issue.
You can find a github issue that explains this in detail [here](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/2601).
Please note you only need to do this once for a new deployment and are using SSL in cases where an SSL certificate doesn't yet exist.

#### Standalone Dashboards

In order to create and share voila dashboards you must lock the following dependency to an older version:

```
simpervisor = "0.4"
```

This is already done in `pyproject.toml`. If you upgrade `simpervisor` to a newer version, it is likely that the stand-alone dashboards will not work.
Note that you will still be able to use jupyterhub + voila from inside juypterhub as expected, only the standalone dashboard will be impacted.


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
  up 						Rebuild the modeling environment and deploys the notebook stack to a k8s cluster
  down 						Tears down the notebook stack
  install 					Install minikube, helm, etc.
  auth 						Authenticate with GCP
  create-image 					Builds docker image for off-platform models
  push-image 					Pushes model docker image to a remote registry
  create-hub-image 				Builds docker image for base jupyterhub service
  push-hub-image 				Push jupyterhub docker image to a remote registry
  start-container <workspace-dir> 		Launches a Docker container and mounts a workspace directory to it
  launch  					Launches jupyterhub on a kubernetes cluster using helm
  stop  					Stops the jupyterhub deployment
  reset-password  <user-email> 			Sends a password reset email for notebook user
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
