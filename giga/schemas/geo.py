from typing import Tuple
from pydantic import BaseModel


LatLonPoint = Tuple[float, float]  # [lat, lon] or (lat, lon)


class UniqueCoordinate(BaseModel):
    """Uniquely identifiable lat/lon coordinate"""

    coordinate_id: str
    coordinate: LatLonPoint  # [lat, lon]


class PairwiseDistance(BaseModel):
    """Distance between uniquely identifiable, ordered coordinates"""

    pair_ids: Tuple[str, str]
    distance: float
    coordinate1: UniqueCoordinate
    coordinate2: UniqueCoordinate
    distance_type: str = "euclidean"
