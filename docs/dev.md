# Giga Dev Documentation

This documentation provides technical details on the Giga model's implementation,
setup, and deployment process.

> Also see the following additional documentation:
> * [User overview](main.ipynb) and details on running each notebook.
> * [Model overview](models.ipynb), including a breakdown of each model.
> * [Model data](data.ipynb), including data schemas and how to update countries.
> * [Model architecture](arch.ipynb), focusing on key parts of the library used for configuration, data aggregation, and model execution.
> * [Python documentation](../dev/documentation.ipynb) automatically generated from the model source code.

### Repository Structure

The python library in this repository is organized into the following key categories to help manage the models and their parameters:

1. Models: the key building blocks of all computations performed by this library
2. Schemas: the definitions of all the model inputs and outputs, data requirements, and configurations
3. Data: the tooling to pull in and transform any external data into formats usable by the library
4. Utilities: helpers for connecting to APIs, visualizing outputs, and constructing inspect able and interactive interfaces
5. App: the application runner for configuring and starting the modeling application

## Local Development
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


## Production Deployment
The production deployment is set up to use Jupyter Hub on Kubernetes. Ideally, one would use a managed Kubernetes service
like Azure Kubernetes Service, AWS Elastic Kubernetes Service or Google Kubernetes Engine.

These are the steps to build the model container and deploy the application to a cluster:
1. Login into your docker container registry. For example `docker login`
2. Build the docker image. We will assume our organization name in the registry is `gigacostmodel`. Run this to build the image `docker build . -t gigacostmodel/cost-model:0.3.12`
3. Push the image to the docker registry by running `docker push gigacostmodel/cost-model:0.3.12`
4. **Note** If you are building the application for the first time, you will want to also build a new jupyterhub image that allows creation of standalone dashboards. This will build an updated jupyterhub image that contains the dashboarding dependencies. Note that this image name is also referenced in the helm values file under `hub.image`. We build this image by running `docker build -f Dockerfile.hub -t gigacostmodel/k8s-hub-cds:2.0.0`
5. Push the docker image to the container registry `docker push gigacostmodel/k8s-hub-cds:2.0.0`
6. Update the `deployment/helm/prod.yaml` to reference these images. In particular update `singleuser.image` to `gigacostmodel/cost-model:0.3.12` and  `hub.image` to use `gigacostmodel/k8s-hub-cds:2.0.0`
7. (Optional) Create the secret for the `MAP_BOX_ACCESS_TOKEN` token that will be used to display the maps. `kubectl create secret generic mapbox-secrets --from-literal=mapbox-token={MAPBOX_TOKEN}`
8. (Optional) Create the secret to access data from the cloud provider. For example a connection string for Azure Data Lake Storage (ADLS) or Google Cloud Credentials. Here is an example for ADLS `kubectl create secret generic azure-secrets --from-literal=adls-connection-string={ADLS_CONNECTION_STRING}`
9. Add the jupyterhub helm chart `helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/` followed by `helm repo update`.
10. Use helm to deploy the jupyter hub application using `helm upgrade --install --values deployment/helm/prod.yaml --version 2.0.0 --timeout 20m`
11. Port forward to the container to make sure you can access it by running `kubectl port-forward svc/proxy-public 8899:80` and then opening `localhost:8899` in your browser.
12. Alternatively, set up Ingres to the cluster. The entrypoint is the `proxy-public` service on port `80`

To build the model container and re-deploy the notebook cluster the run steps 2 to 10.


## Data
There are two options for the data storage used in the application; either local data storage on the device or using a cloud provider like Google Cloud Storage or Azure Blob Storage/Azure Data Lake Storage
### Local Data Storage
To use local data storage, create a folder named `workspace` in the root of thhe project. In here, add two folders, `conf and `data`
1. `conf` contains the configurations for each country in a folder named `countries`
2. `data` contains the school data for each country in a country-specific folder.

Look at the `workspace` folder for an example of how to set up this data

### Cloud Data Storage
Using a cloud provider for data storage is similar to the local data use case. In this case we store the data in a bucket or container from
a cloud service provider's object store for example Google Cloud Storage, Azure Blob Storage or Amazon S3. To use this, create a dedicated bucket or container
and give it a name for example `cost-model` in here, create the same folders as defined under `Local Data Storage` above in the same structure. Take a
look at the `workspace` folder to understand how to structure the data. 

### Selecting the Data Store
Depending on if you're using Local or Cloud data storage, one will have to define the type of data store to use. This is specified in the `giga/data/store/stores.py`
file. Data store implementations exist for the Local Data Store, Google Cloud Storage (GCS) Data store and Azure Data Lake Storage (ADLS) data store. To create an implementation
for another data store for example `Amazon S3` or `minio`, extend the `DataStore` class defined in `giga/data/store/data_store.py`. The ADLS, GCS and local storage options in the
`giga/data/store` folder provide examples of how to extend this class for a different data store.

The data store in use as defined in the ``giga/data/store/stores.py` class , this looks like this by default:
```python
from .data_store import DataStore
from .local_fs_store import LocalFS

# Global Data Store instances. 
LOCAL_FS_STORE: DataStore = LocalFS()

# Configure which storage to use for country data here.
COUNTRY_DATA_STORE: DataStore = LOCAL_FS_STORE

# Storage for schools and costs for now
SCHOOLS_DATA_STORE: DataStore = LOCAL_FS_STORE
```

To use Azure Data Lake Storage (ADLS) change it to this
```python
from .data_store import DataStore
from .adls_store import ADLSDataStore

# Global Data Store instances. 
LOCAL_FS_STORE: DataStore = LocalFS()
GCS_BUCKET_STORE: DataStore = None  # GCSDataStore()
ADLS_CONTAINER_STORE: DataStore = ADLSDataStore()

# Configure which storage to use for country data here.
COUNTRY_DATA_STORE: DataStore = ADLS_CONTAINER_STORE  # LOCAL_FS_STORE  #  GCS_BUCKET_STORE

# Storage for schools and costs for now
SCHOOLS_DATA_STORE: DataStore = ADLSDataStore(container="giga")
```

The process is similar for other data stores.


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
The recommended minimum memory for a single model pod in k8s is 3 GB with a limit of 10 GB.
The current configuration is set to reflect this as follows (from deployment/help/prod.yaml):

```
singleuser:
  # other configs ...
  cpu:
    limit:
    guarantee:
  memory:
    limit: 10G
    guarantee: 3G
```

Do note that no cpu limit is not set above.
Additionally, the somewhat large memory guarantee is needed to run models for all schools in large countries (like Brazil).
If the school data is broken down into smaller sub-regions for those larger countries, it's likely possible to make the memory guarantee significantly smaller.


### Updating the Cluster + Local Testing

You can stop the jupyterhub cluster by running `./stack stop`.
If you need to update the single user image, you can rebuild it using the CLI above.
You can interact with the single user container locally by running `./stack start-container <local-workspace>`.

### Environment Secrets

The deployed application authenticates with a number of backends via deployment and
environment secrets that are not checked in with the application code. 

---
`MAP_BOX_ACCESS_TOKEN` | MapBox API access token string | Used to display detailed country maps during school selection and results visualization.
`OBJSTORE_GCS_CREDS` | JSON service account credentials | Used to connect to Google Cloud APIs, primarily object store
`ADLS_CONNECTION_STRING` | Connection string for ADLS access | Used to connect to Azure Data Lake Storage to get data
---

When deploying the application, you can use deployment secrets to inject these environment
variables, or populate them in an `.env` file in the root folder.

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

### Ingress with Dynamic IP Addresses

If you are unable to specify a static IP address the jupyterhub proxy, you can configure the cluster using a dynamic IP address.
This configuration is managed in the helm values file under the `proxy.service` configurations.
One approach is to make the service port a `NodePort`.
You can read more about other ways of configuring this service [here](https://z2jh.jupyter.org/en/stable/resources/reference.html#proxy-service).

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

## Chart and Plot Visualization

The visualizations in main notebook dashboard are all implemented in python.
They leverage the [pywidgets](https://ipywidgets.readthedocs.io/en/stable/) framework for making UI components and [plotly](https://plotly.com/python/) for creating plots and maps.
Some of the styling and layout is directly defined with CSS.

The visualizations are a direct by-product of the model outputs - they primarily ingest school data and the connectivity cost estimates generated by the models.
The outputs are managed with a helper class to more easily pull out KPIs and other statistics.
You can find the `ResultStats` class under `giga.data.stats.result_stats`.

### Dashboard Layout and Content

The dashboard layout and contents are are managed inside of the `ResultDashboard` class in `viz.notebooks.components.dashboard.result_dashboard`.
You can configure the complete layout of the dashboard inside of the `display` method.
In this method tabs are generated and organized using the `ipywidgets.Tab` component.
With each part of the dashboard being a standalone `Tab` that gets generated by another class method.
For example, the `overview_tab` method creates the overview tab for the dashboard.

### Configuring Styles and Colors

You can configure the colors and map modebars (toolbar at the top right for the maps) inside of `giga.viz.colors` and `giga.viz.plot_configs`.
The color definitions are all pulled in from the colors.py file and include a docstring of where they are used.
The plot_configs.py file contains the modebar configuration, you can read more about valid parameters for this configuration type [here](https://plotly.com/python/configuration-options/#configuration-options).

Additionally, if you want to update any of the styles, colors, or layouts for the main dashboard using CSS, you can update them in `giga.viz.notebooks.components.sections`.
