from pydantic import BaseModel
from typing import List

from giga.schemas.tech import ConnectivityTechnology


class TotalCostScenarioConf(BaseModel):

    scenario_id: str
    technologies: List[ConnectivityTechnology]
    years_opex: int = 5 # the number of opex years to consider in the estimate
