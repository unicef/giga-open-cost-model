from typing import Tuple, List, Dict, Optional
from pydantic import BaseModel, Field
import pandas as pd


LatLonPoint = Tuple[float, float]  # [lat, lon] or (lat, lon)


class UniqueCoordinate(BaseModel):
    """Uniquely identifiable lat/lon coordinate"""

    coordinate_id: str
    coordinate: LatLonPoint  # [lat, lon]
    properties: Dict = None


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


class RawElevationPoint(BaseModel):
    """Response structure from opentopodata API"""

    dataset: str
    elevation: Optional[float] = None
    location: Dict[str, float]

    @staticmethod
    def elevation_point_transformer(data: List[Dict]):
        elevation_point = list(
            map(
                lambda x: RawElevationPoint(
                    dataset=x["dataset"],
                    elevation=x["elevation"],
                    location=x["location"],
                ),
                data,
            )
        )
        return elevation_point


RawElevationProfile = List[RawElevationPoint]


class ElevationPoint(BaseModel):
    """Internal data model used for singular elevation point within the Elevation Profile"""

    coordinates: LatLonPoint
    elevation: Optional[float] = None


class ElevationProfile(BaseModel):
    """Internal data model of a Complete Elevation profile containing multiple elevation points"""

    points: List[ElevationPoint]

    @staticmethod
    def from_raw_elevation_profile(data: RawElevationProfile):
        p = list(
            map(
                lambda x: ElevationPoint(
                    coordinates=[x.location["lat"], x.location["lng"]],
                    elevation=x.elevation,
                ),
                data,
            )
        )
        return ElevationProfile(points=p)
