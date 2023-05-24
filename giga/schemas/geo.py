from typing import Tuple, List, Dict, Optional
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np


LatLonPoint = Tuple[float, float]  # [lat, lon] or (lat, lon)


class UniqueCoordinate(BaseModel):
    """Uniquely identifiable lat/lon coordinate"""

    coordinate_id: str
    coordinate: LatLonPoint = None  # [lat, lon]
    properties: Dict = {}


class UniqueCoordinateTable(BaseModel):
    """A table of uniquely identifiable lat/lon coordinates"""

    coordinates: List[UniqueCoordinate]

    @staticmethod
    def from_csv(file_name):
        try:
            table = pd.read_csv(file_name).to_dict("records")
        except pd.errors.EmptyDataError:
            return UniqueCoordinateTable(coordinates=[])
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

    def to_coordinate_vector(self):
        """Transforms the coordinate table into a numpy vector of coordinates"""
        return np.array([[c.coordinate[0], c.coordinate[1]] for c in self.coordinates])

    def to_data_frame(self):
        """Transforms the coordinate table into a pandas data frame"""
        df = pd.DataFrame([fc.dict() for fc in self.coordinates])
        if len(df) == 0:
            df = pd.DataFrame(columns=["lat", "lon", "coordinate", "coordinate_id"])
        else:
            df["lat"] = df["coordinate"].apply(lambda x: x[0])
            df["lon"] = df["coordinate"].apply(lambda x: x[1])
        return df


class PairwiseDistance(BaseModel):
    """Distance between uniquely identifiable, ordered coordinates"""

    pair_ids: Tuple[str, str]
    distance: float
    coordinate1: UniqueCoordinate
    coordinate2: UniqueCoordinate
    distance_type: str = "euclidean"

    def reversed(self) -> "PairwiseDistance":
        """Returns a new pairwise distance with the coordinates reversed"""
        return PairwiseDistance(
            pair_ids=(self.pair_ids[1], self.pair_ids[0]),
            distance=self.distance,
            coordinate1=self.coordinate2,
            coordinate2=self.coordinate1,
            distance_type=self.distance_type,
        )


class PairwiseDistanceTable(BaseModel):
    """
    A table of pairwise distances between uniquely identifiable, ordered coordinates
    """

    distances: List[PairwiseDistance] = Field(..., min_items=0)

    @staticmethod
    def from_single_lookup(lookup):
        """Transforms a lookup table of distances into a pairwise distance table"""
        distances = [PairwiseDistance(**v) for k, v in lookup.items()]
        return PairwiseDistanceTable(distances=distances)

    @staticmethod
    def from_multi_lookup(lookup):
        """Transforms a lookup table of distances into a pairwise distance table"""
        distances = [
            PairwiseDistance(**e) for k, nearby in lookup.items() for e in nearby
        ]
        return PairwiseDistanceTable(distances=distances)

    def to_edge_table(self):
        """Transforms the pairwise distance table into an edge table"""
        edges = []
        for d in self.distances:
            edges.append(
                {
                    "source": d.coordinate2.coordinate_id,
                    "target": d.coordinate1.coordinate_id,
                    "distance": d.distance,
                }
            )
        return pd.DataFrame(edges)

    def group_by_source(self):
        """Group distances by source coordinate node"""
        grouped = {}
        for d in self.distances:
            try:
                # try to get id of source node from properties
                source_id = d.coordinate1.properties["source"]
                if source_id in grouped:
                    grouped[source_id].append(d)
                else:
                    grouped[source_id] = [d]
            except KeyError:
                grouped[d.coordinate1.coordinate_id] = [d]
        return grouped


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
