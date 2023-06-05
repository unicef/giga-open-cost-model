# Model Notebooks

The project is a collaboration between **[Giga](https://giga.global/)** and **[Actual](https://www.actualhq.com/)**.
The repository contains models for estimating school connectivity costs and deploying them as a standalone application.
This document provides an overview of the Giga model notebooks and provides details on running each notebook. 

### [Cost Estimation Notebook](notebooks/cost-scenario.ipynb)

<br/>

**Jump to section:**
* [Cost estimation notebook](#cost-estimation)
* [Results drilldown notebook](#results-drilldown)
* [Driver notebooks](#driver-notebooks)
* [Model details](#model-details)

> Also see the following additional documentation:
> 
> * [Model Details](docs/models.md)
> * [Model Data Management](docs/data.md)
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

The final section below show electricity availability and costs. For additional visualizations, download your results and see the [drilldown notebook](notebooks/results-drilldown.ipynb).
Click **Download Results** to save model results locally on your computer.

### Scenarios

The following scenarios are available in the model:

- `Lowest Cost`: determines the lowest cost of connectivity for the schools in question by selecting across the available and feasible technologies
- `Fiber Only`: computes the total cost of connecting all the unconnected schools with fiber technology
- `Satellite Only`: computes the total cost of connecting all the unconnected schools with satellite technology
- `Cellular Only`: computes the total cost of connecting all the unconnected schools with cellular technology
- `P2P Only`: computes the total cost of connecting all the unconnected schools with P2P technology

### Parameters

The following parameters can be configured in the model:

* **Scenario**
    * `Cost Scenario` determines which scenario to estimate costs for; either `Minimum Cost` which finds the cheapest technology can be selected, or an individual technology can be selected which will find the costs for just that technology
    * `OpEx Years` determines the number of years that will be considered in the total cost estimates, where total cost is CapEx + OpEx * `OpEx Years`
    * `Bandwidth Demand (Mbps)` determines the expected demand at each school being considered
    * `Use Budget Constraint` flag that allows users to specif a budget, when set will run a constrained optimization on lowest cost or single technology scenarios
    * `Project Budget (Millions USD)` sets the maximum budget for the connectivity project being analyzed, this budget is for the NPV of the project
* **Fiber Model**
    * `Annual cost per Mbps (USD)`: the annual cost of connectivity per Mbps in US Dollars
    * `Cost Per km (USD)` is the average cost of laying fiber lines per km in US Dollars
    * `Maintenance Cost per km (USD)` is the expected annual maintenace cost of new fiber lines in US Dollars
    * `Maximum Connection Length (km)` is the maximum length of an individual fiber connection, if a single fiber connection exceeds this length, it will not be considered feasible
    * `Annual Power Required (kWh)` is the annual power in kWh needed to operate the equipment
    * `Economies of Scale` indicates if an economies of scale approach should be used when estimating the needed length of fiber lines
* **Satellite Model**
    * `Installation Cost (USD)` is the cost of intalling only the technology equipment (no electricity) at the school site
    * `Annual cost per Mbps (USD)`is the annual cost of connectivity per Mbps in US Dollars
    * `Annual Maintenance Cost (USD)` is the annual cost of maintaining the  equipment at the school site
    * `Annual Power Required (kWh)` is the annual power in kWh needed to operate the equipment
* **Cellular Model**
    * `Installation Cost (USD)` is the cost of intalling only the technology equipment (no electricity) at the school site
    * `Annual cost per Mbps (USD)`is the annual cost of connectivity per Mbps in US Dollars
    * `Annual Maintenance Cost (USD)` is the annual cost of maintaining the  equipment at the school site
    * `Annual Power Required (kWh)` is the annual power in kWh needed to operate the equipment
    * `Maximum Cell Tower Range (km)` is the maximum distance from a cell tower that a school can receive internet service
* **P2P Model**
    * `Installation Cost (USD)` is the cost of intalling only the technology equipment (no electricity) both at the school site and at the selected cellular tower
    * `Annual cost per Mbps (USD)`is the annual cost of connectivity per Mbps in US Dollars
    * `Annual Maintenance Cost (USD)` is the annual cost of maintaining the equipment at the school site and at the selected cellular tower
    * `Annual Power Required (kWh)` is the annual power in kWh needed to operate the equipment
    * `Maximum  Range (km)` is the maximum distance from a cell tower that a school can receive internet service
* **Electricity Model**
    * `Cost per kWh (USD)` is the expected average cost of electricity for the schools considered in US Dollars
    * `Solar Total Cost (USD/Watt)` is the average cost of installing solar panels at schools in USD/Watt

---

## Results Drilldown

The [results drilldown notebook](notebooks/results-drilldown.ipynb) allows you to upload the result of a previous model run and visualize/down-select results.

## Country Updates

The [update country notebook](notebooks/dev/update-objstore.ipynb) allows you to update the data associated with each country being hosted temporarily in Google Cloud object storage. See the [data docs](notebooks/docs/data.ipynb) for details.

---

## Driver Notebooks

In addition to the [cost estimation](notebooks/cost-scenario.ipynb), [model validation](notebooks/model-validation.ipynb), and [results drilldown](notebooks/results-drilldown.ipynb) notebooks, the following "driver" notebooks can also be accessed:

* [Model Components](notebooks/drivers/component-drivers.ipynb): demonstrates how key model components can be initialized and run
* [Fiber Model](notebooks/drivers/fiber-model.ipynb): demonstrates how to initialize and run the key nodes in the fiber model
* [Line-of-Sight Model](notebooks/drivers/Line-of-Sight.ipynb): demonstrates how to calculate line-of-sight between entities

---

## Model Details

Each of the connectivity models is briefly described below.
For more details please see [here](docs/models.md).
The cost models are the following:

* **Fiber Model**: asses the costs of connectivity using fiber. Can optionally consider economies of scale, which allows schools that already connected with fiber during modeling to be used as fiber nodes. CapEx considers infrastructure costs of laying fiber, modem/terminal installation costs at school and solar installation if needed. OpEx considers maintenance of fiber infrastructure, maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **Cellular Model**: asses the costs of connectivity using cellular. CapEx considers modem installation at school and solar installation if needed. No other infrastructure costs are considered. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **P2P Model**: asses the cost of connectivity using point to point wireless technology. CapEx considers infrastructure costs of installing a transmitted at a cell tower, modem/terminal installation costs at school and solar installation if needed. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.
* **Satellite Model**: asses the cost of connectivity using LEO satellite. CapEx considers terminal installation at school and solar installation if needed. OpEx considers maintenance of equipment at school, costs of internet at the school, and electricity costs.

All modeling capabilities are defined within `giga/models`. The models are further broken down into the following categories:

* Nodes: atomic, modular building blocks that contain a computation, transformation, or external data
* Components: stacks nodes together with a clear and specific purpose (e.g. use case driven - compute cost of fiber connection) prepares the models to join into the entities that solve a specific problem
* Scenarios: drives the computation by piecing together multiple components and solving a specific problem by deriving a key result. Allows same components to serve multiple purposes: e.g. answer the questions of what is the cost of connecting all schools in Rwanda to the internet? VS If there is a budget of $10M which schools should be connected to maximize the number of students with internet access?
