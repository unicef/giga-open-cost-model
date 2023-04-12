from pydantic import BaseModel, validator
from typing import List, Literal, Union
import math


class ElectricityCapexConf(BaseModel):

    solar_panel_costs: float  # USD
    battery_costs: float  # USD


class ElectricityOpexConf(BaseModel):

    cost_per_kwh: float  # USD


class ElectricityCostConf(BaseModel):

    capex: ElectricityCapexConf
    opex: ElectricityOpexConf


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

    cost_per_km: float
    annual_bandwidth_cost_per_mbps: float = 0.0


class FiberCapex(BaseModel):

    cost_per_km: float  # USD
    fixed_costs: float = 0.0  # USD
    economies_of_scale: bool = True


class FiberConstraints(BaseModel):

    maximum_connection_length: float = math.inf  # meters
    maximum_bandwithd: float = 2_000  # Mbps
    required_power: float = 500  # annual kWh


class CellularConstraints(BaseModel):

    maximum_range: float = math.inf  # meters
    maximum_bandwithd: float = 2_000  # Mbps
    required_power: float = 500  # annual kWh

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
    P2PTechnologyCostConf
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


class MinimumCostScenarioConf(BaseModel):
    """
    Configuration for a model scenario that estimates minimum budget
    necessary to connect schools with the cheapest technology when available
    """

    scenario_id: Literal["minimum_cost", "budget_constrained"] = "minimum_cost"
    technologies: List[TechnologyConfiguration]
    years_opex: int = 5  # the number of opex years to consider in the estimate
    opex_responsible: Literal[
        "Provider", "Consumer", "Both"
    ]  # type of opex costs to consider
    bandwidth_demand: float  # Mbps
    cost_minimizer_config: CostMinimizerConf = None

    class Config:
        case_sensitive = False

    @validator("cost_minimizer_config", always=True)
    def validate_minimizer_conf(cls, value, values):
        return CostMinimizerConf(years_opex=values["years_opex"])
