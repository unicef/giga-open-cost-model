# Model Notebooks

The project is a collaboration between **[Giga](https://giga.global/)** and **[Actual](https://www.actualhq.com/)**.
The repository contains models for estimating school connectivity costs and deploying them as a standalone application.
This document provides an overview of the Giga model notebooks and provides details on running each notebook. 

### [Cost Estimation Notebook](notebooks/cost-scenario.ipynb)

<br/>

**Jump to section:**
* [Cost estimation notebook](#cost-estimation)
* [Driver notebooks](#driver-notebooks)
* [Model details](#model-details)

> Also see the following additional documentation:
> 
> * [Model Notebooks](notebooks/docs/main.ipynb)
> * [Model Details](notebooks/docs/models.ipynb)
> * [Model Data Management](notebooks/docs/data.ipynb)
> * [Model Library Architecture](docs/arch.md)
> * [Developer documentation](docs/dev.md)

The notebooks are used for two primary purposes:

1. Serve as interactive dashboard through which models can be configured, executed, and their outputs analyzed.
2. Serve as tutorials or example "drivers" of how a particular model can be used.
---

## Cost Estimation

The [cost estimation notebook](notebooks/cost-scenario.ipynb) provides an modeling interface for estimating the total cost of connecting a group of schools. It estimates the CapEx, OpEx, and NPV connectivity costs by technology and using the cheapest technologies.

This notebook provides an modeling interface for estimating the total cost of connecting a group of schools. The process is broken down into three steps:
* **I. Configuration**: where you can configure a variety of model parameters
* **II. Run the Model**: where you can start the model execution
* **III. Results**: where you can examine the results in tables and plots and download them locally

Note that the notebook is interactive.
Namely, you can update the configurations, run the models again, and generate a new set of outputs.
You will need to explicitly re-run the models again after a re-configuration (by clicking the `Run Model` button), and you will need to explicitly re-generate the outputs (by clicking the various `Generate ...` buttons) to see the ouputs updated.

If you would like to upload a configuration from a local machine, use the `Import Config` button to populate the configuration sets from a local file.

Once you have finalized or updated the configuration above, click **Run Model** to generate new results and display summary tables that show aggregated cost statistics across the schools of interest. 

The final section below show electricity availability and costs.
Click **Download Results** to save model results locally on your computer.

## Country Updates

The [update country notebook](notebooks/dev/update-objstore.ipynb) allows you to update the data associated with each country being hosted temporarily in Google Cloud object storage. See the [data docs](notebooks/docs/data.ipynb) for details.

---

## Driver Notebooks

In addition to the [cost estimation](notebooks/cost-scenario.ipynb), and [model validation](notebooks/model-validation.ipynb) the following "driver" notebooks can also be accessed:

* [Model Components](notebooks/drivers/component-drivers.ipynb): demonstrates how key model components can be initialized and run
* [Fiber Model](notebooks/drivers/fiber-model.ipynb): demonstrates how to initialize and run the key nodes in the fiber model
* [Line-of-Sight Model](notebooks/drivers/Line-of-Sight.ipynb): demonstrates how to calculate line-of-sight between entities

---

## Model Details

Each of the connectivity models is briefly described below.
For more details please see [here](notebooks/docs/models.ipynb).
The cost models are the following:

* **Fiber Model**: asses the costs of connectivity using fiber. Can optionally consider economies of scale, which allows schools that already connected with fiber during modeling to be used as fiber nodes. CapEx considers infrastructure costs of laying fiber, modem/terminal installation costs at school and solar installation if needed. OpEx considers maintenance of fiber infrastructure, maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **Cellular Model**: asses the costs of connectivity using cellular. CapEx considers modem installation at school and solar installation if needed. No other infrastructure costs are considered. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **P2P Model**: asses the cost of connectivity using point to point wireless technology. CapEx considers infrastructure costs of installing a transmitted at a cell tower, modem/terminal installation costs at school and solar installation if needed. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **Satellite Model**: asses the cost of connectivity using LEO satellite. CapEx considers terminal installation at school and solar installation if needed. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.

All modeling capabilities are defined within `giga/models`. The models are further broken down into the following categories:

* Nodes: atomic, modular building blocks that contain a computation, transformation, or external data
* Components: stacks nodes together with a clear and specific purpose (e.g. use case driven - compute cost of fiber connection) prepares the models to join into the entities that solve a specific problem
* Scenarios: drives the computation by piecing together multiple components and solving a specific problem by deriving a key result. Allows same components to serve multiple purposes: e.g. answer the questions of what is the cost of connecting all schools in Rwanda to the internet? VS If there is a budget of $10M which schools should be connected to maximize the number of students with internet access?
