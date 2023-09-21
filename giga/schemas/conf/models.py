from pydantic import BaseModel, validator, FilePath
from typing import List, Literal, Union
import math

METERS_IN_KM = 1_000.0


class ElectricityCapexConf(BaseModel):

    solar_cost_per_watt: float  # USD/Watt


class ElectricityOpexConf(BaseModel):

    cost_per_kwh: float  # USD

class ElectricityConstraints(BaseModel):

    required_power_per_school: float #Watts
    allow_new_electricity: bool = True

class ElectricityCostConf(BaseModel):

    capex: ElectricityCapexConf
    opex: ElectricityOpexConf
    constraints: ElectricityConstraints

class BandwidthCost(BaseModel):

    bandwidth_threshold: float  # Mbps
    annual_cost: float  # USD


class GeneralizedInternetCapex(BaseModel):

    fixed_costs: float = 0.0  # USD


class GeneralizedInternetOpex(BaseModel):

    fixed_costs: float = 0.0  # USD
    annual_bandwidth_cost_per_mbps: float = 0.0


class GeneralizedInternetConstraints(BaseModel):

    maximum_bandwithd: float = 2_000  # Mbps
    required_power: float = 10  # annual kWh


class FiberOpex(BaseModel):

    fixed_costs: float = 0.0  # USD
    cost_per_km: float
    annual_bandwidth_cost_per_mbps: float = 0.0


class FiberCapex(BaseModel):

    cost_per_km: float  # USD
    fixed_costs: float = 0.0  # USD
    economies_of_scale: bool = True
    schools_as_fiber_nodes: bool = True


class FiberConstraints(BaseModel):

    maximum_connection_length: float = math.inf  # meters
    maximum_bandwithd: float = 2_000  # Mbps
    required_power: float = 500  # annual kWh


class CellularConstraints(BaseModel):

    maximum_range: float = math.inf  # meters
    maximum_bandwithd: float = 2_000  # Mbps
    required_power: float = 500  # annual kWh
    valid_cellular_technologies: List[str] = ["4G", "LTE"]


class P2PConstraints(BaseModel):

    # Can get these values from Giga / figure out reasonable defaults for P2P
    maximum_range: float = math.inf  # meters
    maximum_bandwithd: float = 2_000  # Mbps
    required_power: float = 500  # annual kWh


class FiberTechnologyCostConf(BaseModel):
    capex: FiberCapex
    opex: FiberOpex
    constraints: FiberConstraints
    technology: str = "Fiber"
    electricity_config: ElectricityCostConf = None


class SatelliteTechnologyCostConf(BaseModel):
    capex: GeneralizedInternetCapex
    opex: GeneralizedInternetOpex
    constraints: GeneralizedInternetConstraints
    technology: str = "Satellite"
    electricity_config: ElectricityCostConf = None


class CellularTechnologyCostConf(BaseModel):
    capex: GeneralizedInternetCapex
    opex: GeneralizedInternetOpex
    constraints: CellularConstraints
    technology: str = "Cellular"
    electricity_config: ElectricityCostConf = None


class P2PInternetCapex(GeneralizedInternetCapex):
    tower_fixed_costs: float = 0.0  # USD


class P2PTechnologyCostConf(BaseModel):
    capex: P2PInternetCapex
    opex: GeneralizedInternetOpex
    constraints: P2PConstraints
    # max range, signal strength, etc. see CellularConstarint
    technology: str = "P2P"
    electricity_config: ElectricityCostConf = None


TechnologyConfiguration = Union[
    FiberTechnologyCostConf,
    SatelliteTechnologyCostConf,
    CellularTechnologyCostConf,
    P2PTechnologyCostConf,
]


class CostMinimizerConf(BaseModel):

    years_opex: int = 5
    budget_constraint: float = math.inf  # USD
    economies_of_scale: bool = True


class SingleTechnologyScenarioConf(BaseModel):
    """
    Configuration for a model scenario that estimates connectivity budget
    for a single selected technology
    """

    scenario_id: str = "single_tech_cost"
    technology: Literal["Fiber", "Cellular", "Microwave", "Satellite", "P2P"]
    years_opex: int = 5
    opex_responsible: Literal[
        "Provider", "Consumer", "Both"
    ]  # type of opex costs to consider
    bandwidth_demand: float  # Mbps
    tech_config: TechnologyConfiguration

    class Config:
        case_sensitive = False

    @property
    def maximum_bandwidths(self):
        return {self.technology: self.tech_config.constraints.maximum_bandwithd}


class SATSolverConf(BaseModel):
    """
    Configuration for the SAT solver
    """

    sat_engine: bool = False
    road_data: bool = False
    time_limit: int = 600  # seconds
    do_hints: bool = False
    num_workers: int = 16
    search_log: bool = False
    load_relational_graph_path: FilePath = None
    write_relational_graph_path: FilePath = None

    @property
    def cost_per_m(self):
        # convert cost per km to cost per m for SAT solver
        # round up to ensure that we don't underestimate the cost
        return math.ceil(self.cost_per_km / METERS_IN_KM)


class MinimumCostScenarioConf(BaseModel):
    """
    Configuration for a model scenario that estimates minimum budget
    necessary to connect schools with the cheapest technology when available
    """

    scenario_id: Literal["minimum_cost", "single_tech_cost"] = "minimum_cost"
    technologies: List[TechnologyConfiguration] = None
    years_opex: int = 5  # the number of opex years to consider in the estimate
    opex_responsible: Literal[
        "Provider", "Consumer", "Both"
    ]  # type of opex costs to consider
    bandwidth_demand: float  # Mbps
    required_power_per_school: float = 0 #Watts
    single_tech: Literal[
        "Fiber", "Cellular", "Satellite", "P2P"
    ] = None  # if not None, only consider this technology
    cost_minimizer_config: CostMinimizerConf = None
    sat_solver_config: SATSolverConf = SATSolverConf()

    class Config:
        case_sensitive = False

    @validator("cost_minimizer_config", always=True)
    def validate_minimizer_conf(cls, value, values):
        return CostMinimizerConf(years_opex=values["years_opex"])

    @property
    def maximum_bandwidths(self):
        return {
            t.technology: t.constraints.maximum_bandwithd for t in self.technologies
        }

    @property
    def includes_fiber(self):
        return any([t.technology == "Fiber" for t in self.technologies])
    
class PriorityScenarioConf(BaseModel):
    """
    Configuration for a model scenario that estimates minimum budget
    necessary to connect schools with the cheapest technology when available
    """

    scenario_id: str = "priority_cost"
    technologies: List[TechnologyConfiguration] = None
    years_opex: int = 5  # the number of opex years to consider in the estimate
    opex_responsible: Literal[
        "Provider", "Consumer", "Both"
    ]  # type of opex costs to consider
    bandwidth_demand: float  # Mbps
    required_power_per_school: float = 0 #Watts
    single_tech: Literal[
        "Fiber", "Cellular", "Satellite", "P2P"
    ] = None  # if not None, only consider this technology
    cost_minimizer_config: CostMinimizerConf = None
    sat_solver_config: SATSolverConf = SATSolverConf()

    class Config:
        case_sensitive = False

    @validator("cost_minimizer_config", always=True)
    def validate_minimizer_conf(cls, value, values):
        return CostMinimizerConf(years_opex=values["years_opex"])

    @property
    def maximum_bandwidths(self):
        return {
            t.technology: t.constraints.maximum_bandwithd for t in self.technologies
        }

    @property
    def includes_fiber(self):
        return any([t.technology == "Fiber" for t in self.technologies])
