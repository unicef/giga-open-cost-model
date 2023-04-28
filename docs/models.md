# Model Documentation

Key model components are outlined below.
Their architecture is presented in diagram format and code snippet examples are shown as well.
As a reminder a model component is differentiated from a model node in the following way:

* Nodes: atomic, modular building blocks that contain a computation, transformation, or serve external data
* Components: stacks nodes together with a clear and specific purpose (e.g. use case driven - compute cost of fiber connection) prepares the models to join into the entities that solve a specific problem
* Scenarios: drives the computation by piecing together multiple components and solving a specific problem by deriving a key result. Allows same components to serve multiple purposes: e.g. answer the questions of what is the cost of connecting all schools in Rwanda to the internet? VS If there is a budget of $10M which schools should be connected to maximize the number of students with internet access?

## Fiber Cost Model

Documentation of the fiber cost model can be found below.

* **Description**: estimates the CapEx and annual OpEx costs of connecting a school to the internet using fiber.
Considers economies of scale by default which assumes schools that have been connected to a fiber network can be used as fiber nodes for unconnected schools.  
* **Sub-models**:
	* Distance model: computes distances between point pairs (default is Haversine distance)
	* Connection model: connects a set of unconnected components (e.g. schools) to connected components (e.g. fiber nodes). Default is a greedy connect model that connects closest unconnected components to one that is connected. The default configuration assumes that unconnected components can can also be used as connections after they've been connected. This enables the economies of scale heuristic.
* **Parameters**: the full configuration set for the fiber models can be found [here](#fiber-model-configuration), the parameters exposed to users can be found below:
	* `Annual cost per Mbps (USD)`: the annual cost of connectivity per Mbps in US Dollars
    * `Cost Per km (USD)` is the average cost of laying fiber lines per km in US Dollars
    * `Maintenance Cost per km (USD)` is the expected annual maintenace cost of new fiber lines in US Dollars
    * `Maximum Connection Length (km)` is the maximum length of an individual fiber connection, if a single fiber connection exceeds this length, it will not be considered feasible
    * `Annual Power Required (kWh)` is the annual power in kWh needed to operate the equipment
    * `Economies of Scale` indicates if an economies of scale approach should be used when estimating the needed length of fiber lines
* **Data Inputs**: the typically external data needed to drive the models are outlined below. Please note that data inputs are accessible to model components through the `DataSpace` client.
	* Fiber node locations, as lat/lon coordinates, definition can be found [here](#unique-coordinate)
	* School entities, which includes coordinates and other properties, definition can be found [here](#school-entity)
* **Outputs**: the fiber generates a collection of connection costs for each school considered. The connection costs contain both CapEx and OpEx estimates. The definition for a single school cost can be found [here](#school-connection-cost)




### Architecture

The fiber model consists of the following sub-models:

* Distance model node for computing distances between two points. A custom implementation can be used instead of the default Haversine distance model.
* Connector model node used to identify feasible connections between points. A greedy distance connector model is the default. It connects unconnected components (e.g. schools) to connected components (e.g. fiber nodes) by picking the closest components first, where closest is determined by the distance model node.
* Electricity model component for estimating the electricity costs associated with installing and operating the internet technology.

The outline of the fiber model component architecture is shown in the diagram below.
The green shaded boxes indicate models for which a custom node could be implemented with a different capability.
For example, the default distance metric used in estimating fiber costs is Haversine, if a distance metric along known roads was desired, a new node implementation that calculates that distance between two points can be substituted to derive a different set of results.

![alt text](res/fiber-architecture.png "Fiber Model")  

### Implementation Example

For an in-depth model "driver" that provides an in-depth overview of how the fiber model works, see the notebook [here](../notebooks/fiber-model.ipynb).
The example below shows how a custom distance model can be used in a fiber model component.
Please note that the custom model below `RoadLengthDistance` is not currently part of the library and is simply an example.

```python
from giga.models.components.fiber_cost_model import FiberCostModel
from giga.schemas.conf.models import FiberTechnologyCostConf

# Specify all the configurations, there are parsers that can help with this in the library
config = FiberTechnologyCostConf(
            capex={
                "cost_per_km": 7_500, # USD
                "economies_of_scale": True,
            },
            opex={
                "cost_per_km": 100, # USD
                "annual_bandwidth_cost_per_mbps": 10, # in USD
            },
            constraints={
                "maximum_connection_length": 20, # km
                "required_power": 500, # in kWh
                "maximum_bandwithd": 2_000.0, # mbps
            },
        )

# Use a custom implementation for distance model (this is an example)
custom_distance_model = RoadLengthDistance() # Note this is an example, must expose a `run` method

# Get the school data
schools = ... # a number of ways to load this including from project connect APIs

# create and run the mode
model = FiberCostModel(config)
outputs = model.run(schools,
                    distance_model=custom_distance_model) # pass in the model at runtime
```


## Cellular Cost Model

Documentation of the cellular cost model can be found below.

* **Description**: estimates the CapEx and annual OpEx costs of connecting a school to the internet using cellular technology.
* **Sub-models**:
	* Distance model: computes distances between point pairs (default is Haversine distance)
* **Parameters**: the full configuration set for the fiber models can be found [here](#fiber-model-configuration), the parameters exposed to users can be found below:
    * `Installation Cost (USD)` is the cost of intalling only the technology equipment (no electricity) at the school site
    * `Annual cost per Mbps (USD)`is the annual cost of connectivity per Mbps in US Dollars
    * `Annual Maintenance Cost (USD)` is the annual cost of maintaining the  equipment at the school site
    * `Annual Power Required (kWh)` is the annual power in kWh needed to operate the equipment
    * `Maximum Cell Tower Range (km)` is the maximum distance from a cell tower that a school can receive internet service
* **Data Inputs**: the typically external data needed to drive the models are outlined below. Please note that data inputs are accessible to model components through the `DataSpace` client.
	* School entities, which includes coordinates and other properties, definition can be found [here](#school-entity)
	* OPTIONAL: Cell tower locations, as lat/lon coordinates, definition can be found [here](#cell-tower)
    * OPTIONAL: Existing coverage at the school of interest
* **Outputs**: the cellular model generates a collection of connection costs for each school considered. The connection costs contain both CapEx and OpEx estimates. The definition for a single school cost can be found [here](#school-connection-cost)

**Description**: there are two steps to the cellular mode: 1. assessment of cellular coverage at a school, 2. cost calculations.
The assessment of cellular coverage can take on two forms - schools is considered to have coverage if it is within a given range of existing cell tower infrastructure OR if the cellular coverage has been included as a property in the school definition as part of supplemental school data.


## Implementing a Model

You can implement a new technology by adding a new model component.
You can find the notebook [here](../notebooks/drivers/model-component-example.ipynb) that walks through the details of the implementation.
In order to fully integrate a new model component into the notebook application, you'll need to complete the following additional steps:
1. Extend the data schemas for technology definitions and scenarios to include the new technology model  
2. Extend the scenario implementation you would like this technology to be available in
3. Update the notebook UI to include the configurable cost drivers of this scenario 

