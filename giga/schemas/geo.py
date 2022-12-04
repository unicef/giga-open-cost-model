from typing import Tuple, List
from pydantic import BaseModel, Field
import pandas as pd


LatLonPoint = Tuple[float, float]  # [lat, lon] or (lat, lon)


class UniqueCoordinate(BaseModel):
    """Uniquely identifiable lat/lon coordinate"""

    coordinate_id: str
    coordinate: LatLonPoint  # [lat, lon]


class UniqueCoordinateTable(BaseModel):
    """A table of uniquely identifiable lat/lon coordinates"""

    coordinates: List[UniqueCoordinate] = Field(..., min_items=1)

    @staticmethod
    def from_csv(file_name):
        table = pd.read_csv(file_name).to_dict("records")
        coords = list(
            map(
                lambda x: UniqueCoordinate(
                    coordinate_id=x["coordinate_id"], coordinate=[x["lat"], x["lon"]]
                ),
                table,
            )
        )
        return UniqueCoordinateTable(coordinates=coords)

    def to_csv(self, file_name: str):
        tabular = list(
            map(
                lambda x: {
                    "coordinate_id": x.coordinate_id,
                    "lat": x.coordinate[0],
                    "lon": x.coordinate[1],
                },
                self.coordinates,
            )
        )
        pd.DataFrame(tabular).to_csv(file_name)


class PairwiseDistance(BaseModel):
    """Distance between uniquely identifiable, ordered coordinates"""

    pair_ids: Tuple[str, str]
    distance: float
    coordinate1: UniqueCoordinate
    coordinate2: UniqueCoordinate
    distance_type: str = "euclidean"
