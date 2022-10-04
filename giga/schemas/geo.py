from typing import List, Tuple
from pydantic import BaseModel


LatLonPoint = Tuple[float, float] # [lat, lon] or (lat, lon)

class UniqueCoordinate(BaseModel):
    """Uniquely identifiable lat/lon coordinate"""

    id: str
    coordainte: LatLonPoint # [lat, lon]
