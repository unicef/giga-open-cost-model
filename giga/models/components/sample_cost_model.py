from pydantic import BaseModel, validate_arguments

from giga.utils.progress_bar import progress_bar as pb
from giga.schemas.output import CostResultSpace, SchoolConnectionCosts
from giga.utils.logging import LOGGER
from giga.data.space.model_data_space import ModelDataSpace


class SampleTechnologyCostConf(BaseModel):
    """
    Sample cost drivers all in USD
    """

    cost_parameter_a: float  # the cost of capex per school
    cost_parameter_b: float  # the cost of opex for a connected school
    cost_parameter_c: float  # the cost of opex for an unconnected school


class SampleCostModel:
    """
    A sample cost model that assigns a cost to each school based on constant parameters
    """

    def __init__(self, config: SampleTechnologyCostConf):
        self.config = config

    def compute_cost(self, school: ModelDataSpace) -> SchoolConnectionCosts:
        # if connected assign cost_parameter_b to opex otherwise cost_parameter_x
        opex = (
            self.config.cost_parameter_b
            if school.connected
            else self.config.cost_parameter_c
        )
        return SchoolConnectionCosts(
            school_id=school.giga_id,
            capex=self.config.cost_parameter_a,
            capex_provider=self.config.cost_parameter_a,
            capex_consumer=0.0,
            opex=opex,
            opex_provider=0.0,  # assume no cost attribution to provider
            opex_consumer=opex,
            technology="None",  # a valid technology type can be None
        )

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def run(
        self, data_space: ModelDataSpace, progress_bar: bool = False
    ) -> CostResultSpace:
        """
        Computes a cost table for schools present in the data_space input
        """
        LOGGER.info(f"Starting Sample Cost Model")
        # we can access different types of data in the data_space client, let's grab the schools
        schools = data_space.school_entities
        iterable = pb(schools) if progress_bar else schools  # creates a progress bar
        costs = [self.compute_cost(s) for s in iterable]
        return CostResultSpace(
            technology_results={"model_type": "Sample"}, cost_results=costs,tech_name="sample"
        )
