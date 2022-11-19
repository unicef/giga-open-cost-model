from enum import Enum
from typing import List
from pydantic import BaseModel, Field
import pandas as pd

from giga.data.transforms.giga_format import cell_towers_to_standard_format
from giga.schemas.geo import UniqueCoordinate


class CellTechnology(str, Enum):
    """Valid level of education"""

    two_g = "2G"
    three_g = "3G"
    four_g = "4G"


class CellularTower(BaseModel):
    """Definition for a single cell tower"""

    tower_id: str
    operator: str
    outdoor: bool
    lat: float
    lon: float
    height: float
    technologies: List[CellTechnology]

    class Config:
        use_enum_values = True

    def to_coordinates(self):
        """ Transforms the cell tower into a simplified coordinate """
        return UniqueCoordinate(coordinate_id=self.tower_id,
                                coordinate=[self.lat, self.lon])


class CellTowerTable(BaseModel):
    """A table or collection of cell towers"""

    towers: List[CellularTower] = Field(..., min_items=1)

    @staticmethod
    def from_csv(file_name: str, giga_format: bool = True):
        frame = pd.read_csv(file_name, keep_default_na=False)
        if giga_format:
            # reformat from giga format into internal model format
            frame = cell_towers_to_standard_format(frame)
        return CellTowerTable(towers=frame.to_dict('records'))

    def to_coordinates(self):
        """ Transforms the cell tower table into a table of simplified coordinate """
        return [s.to_coordinates() for s in self.towers]
