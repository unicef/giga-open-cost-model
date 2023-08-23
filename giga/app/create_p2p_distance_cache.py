#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
import os
import argparse
import math

from giga.utils.logging import LOGGER
from typing import List, Dict

from giga.models.nodes.elevation.elevation_profile_generator import (
    ElevationProfileGenerator,
)
#from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.school import GigaSchoolTable
from giga.schemas.cellular import CellTowerTable, CellularTower
from giga.schemas.geo import (
    UniqueCoordinate,
    ElevationProfile,
    LatLonPoint,
    PairwiseDistance,
)
from giga.models.nodes.elevation.line_of_sight_model import LineofSightModel
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.schemas.distance_cache import (
    SingleLookupDistanceCache,
    MultiLookupDistanceCache,
)
from giga.utils.progress_bar import progress_bar as pb
import json
import pickle

class P2PCacheCreatorArgs:
    workspace_directory: str = None
    n_chunks: int = 100
    n_nearest_neighbors: int = 20
    n_elevation_profile_samples: int = 4
    maximum_distance_meters: float = math.inf
    los_buffer_meters: float = 5
    receiver_height_meters: float = 5
    progress_bar: bool = True
    file_suffix: str = "_cache"
    export_to_file: bool = True


class P2PCacheCreator:
    args: P2PCacheCreatorArgs = None

    def __init__(self, args: P2PCacheCreatorArgs):
        self.args = args
        self._towers: Dict[UniqueCoordinate, CellularTower] = None
        self._school_coords: List[UniqueCoordinate] = None
        self._egp: ElevationProfileGenerator = ElevationProfileGenerator()
        self._los: LineofSightModel = LineofSightModel()

    # Mapping from coordinate ID (== tower ID) to tower.
    @property
    def towers(self) -> Dict[str, CellularTower]:
        if self._towers is None:
            cell_tower_table = CellTowerTable.from_csv(
                os.path.join(self.args.workspace_directory, "cellular.csv")
            )
            self._towers = {
                t.to_coordinates().coordinate_id: t for t in cell_tower_table.towers
            }
        return self._towers

    @property
    def school_coords(self) -> List[UniqueCoordinate]:
        if self._school_coords is None:
            school_table = GigaSchoolTable.from_csv(
                os.path.join(self.args.workspace_directory, "schools.csv")
            )
            self._school_coords = school_table.to_coordinates()
        return self._school_coords

    def closest_towers(self) -> List[PairwiseDistance]:
        """
        Returns merged list of closest towers for each school.
        """
        dist_model = VectorizedDistanceModel(
            progress_bar=self.args.progress_bar,
            n_nearest_neighbors=self.args.n_nearest_neighbors,
            maximum_distance=self.args.maximum_distance_meters,
        )
        tower_coords = [t.to_coordinates() for t in self.towers.values()]
        return dist_model.run_chunks(
            (self.school_coords, tower_coords),
            n_chunks=self.args.n_chunks,
        )

    def prune_obstructed_towers(
        self, school_coord: UniqueCoordinate, pairs: List[PairwiseDistance]
    ) -> List[PairwiseDistance]:
        towers: List[CellularTower] = [
            self.towers[d.coordinate1.coordinate_id] for d in pairs
        ]
        coords = [
            [school_coord.coordinate, t.to_coordinates().coordinate] for t in towers
        ]
        profiles: List[ElevationProfile] = self._egp.run(
            coords, samples=self.args.n_elevation_profile_samples
        )

        # Account for height buffer, school receiver height, and cell tower height.
        for ep, tower in zip(profiles, towers):
            ep.points[0].elevation += self.args.receiver_height_meters
            ep.points[-1].elevation += tower.height
            for pt in ep.points[1:-1]:
                pt.elevation += self.args.los_buffer_meters

        los_results: List[bool] = self._los.run(profiles)
        return [p for p, has_los in zip(pairs, los_results) if has_los]

    def run(self) -> SingleLookupDistanceCache:
        # Temporary distance cache used to as input for LOS calculation.
        dists_towers: MultiLookupDistanceCache = (
            MultiLookupDistanceCache.from_distances(self.closest_towers())
        )
        with open("aux_dists_towers.json", "w") as f:
            json.dump(dists_towers.dict(), f)

        # Accumulate list of closest visible towers for each school.
        closest_visible_towers: List[PairwiseDistance] = []
        iterable = (
            pb(self.school_coords) if self.args.progress_bar else self.school_coords
        )
        i = 0
        for school_coord in iterable:
            if school_coord.coordinate_id not in dists_towers.lookup:
                continue
            closest_pairs: List[PairwiseDistance] = dists_towers.lookup[
                school_coord.coordinate_id
            ]
            closest_visible_towers += self.prune_obstructed_towers(
                school_coord, closest_pairs
            )
            i += 1
            if i%1000==0:
                to_save = {"index":i,"closest_visible_towers":closest_visible_towers}
                with open("aux_closest_visible_towers.pkl", "w") as f:
                    pickle.dump(to_save, f)

        # Build and return the final cache.
        dist_cache = [p.reversed() for p in closest_visible_towers]
        p2p_cache = SingleLookupDistanceCache.from_distances(dist_cache)
        if self.args.export_to_file:
            p2p_cache.to_json(
                os.path.join(
                    self.args.workspace_directory, f"p2p{self.args.file_suffix}.json"
                )
            )


def main():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("required arguments")
    required.add_argument("--workspace-directory", "-w", required=True)
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "--n-chunks",
        "-nc",
        type=int,
        default=100,
        help="Specifies the number of chunks to split the distance matrix into",
    )
    optional.add_argument(
        "--n-nearest-neighbors",
        "-nn",
        type=int,
        default=20,
        help="Specifies the number of nearest neighbors to use for the distance cache",
    )
    optional.add_argument(
        "--maximum-distance-meters",
        "-md",
        type=float,
        default=math.inf,
        help="Specifies the maximum distance to consider for the distance model",
    )
    optional.add_argument(
        "--file-suffix",
        "-fs",
        type=str,
        default="_cache",
        help="Specifies the suffix to use for the cache file",
    )
    optional.add_argument(
        "--n-elevation-profile-samples",
        "-es",
        type=int,
        default=4,
        help="Specifies the number of samples to use for the elevation profile",
    )
    optional.add_argument(
        "--los-buffer-meters",
        "-lb",
        type=float,
        default=5,
        help="Specifies the buffer to use for the line-of-sight model",
    )
    optional.add_argument(
        "--receiver-height-meters",
        "-rh",
        type=float,
        default=5,
        help="Specifies the height of the school-side receiver in meters",
    )
    args: P2PCacheCreatorArgs = parser.parse_args()
    args.progress_bar = True
    args.export_to_file = True
    P2PCacheCreator(args).run()


if __name__ == "__main__":
    main()
