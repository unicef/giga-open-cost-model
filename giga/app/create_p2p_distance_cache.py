#!/usr/bin/env python3

import os
import argparse
import logging
import math

from giga.utils.logging import LOGGER
import pandas as pd
from typing import List, Dict, Tuple

from giga.models.nodes.elevation.elevation_profile_generator import ElevationProfileGenerator
from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.school import GigaSchoolTable
from giga.schemas.cellular import CellTowerTable
from giga.schemas.geo import UniqueCoordinate, ElevationProfile, LatLonPoint, PairwiseDistance
from giga.models.nodes.elevation.line_of_sight_model import LineofSightModel
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.schemas.distance_cache import (
    SingleLookupDistanceCache,
    MultiLookupDistanceCache,
)


class P2PCacheCreatorArgs():
    workspace_directory: str = None
    n_chunks: int = 100
    n_nearest_neighbors: int = 20
    n_elevation_profile_samples: int = 4
    maximum_distance_meters: float = math.inf
    file_suffix: str = "_cache"


class P2PCacheCreator():
    args: P2PCacheCreatorArgs = None

    def __init__(self, args: P2PCacheCreatorArgs):
        self.args = args
        self._tower_coords: List[UniqueCoordinate] = None
        self._school_coords: List[UniqueCoordinate] = None

    def closest_towers(self) -> List[PairwiseDistance]:
        """
        Returns merged list of closest towers for each school.
        """
        model = VectorizedDistanceModel(
            progress_bar=True,
            n_nearest_neighbors=self.args.n_nearest_neighbors,
            maximum_distance=self.args.maximum_distance_meters,
        )
        return model.run_chunks(
            (self.school_coords, self.tower_coords),
            n_chunks=self.args.n_chunks,
        )

    @property
    def tower_coords(self) -> List[UniqueCoordinate]:
        if self._tower_coords is None:
            cell_tower_table = CellTowerTable.from_csv(
                os.path.join(self.args.workspace_directory, "cellular.csv")
            )
            self._tower_coords = cell_tower_table.to_coordinates()
        return self._tower_coords

    @property
    def school_coords(self) -> List[UniqueCoordinate]:
        if self._school_coords is None:
            school_table = GigaSchoolTable.from_csv(
                os.path.join(self.args.workspace_directory, "schools.csv")
            )
            self._school_coords = school_table.to_coordinates()
        return self._school_coords

    def run(self) -> None:
        LOGGER.info(f"towers: {len(self.tower_coords)}")
        LOGGER.info(f"schools: {len(self.school_coords)}")
        # Temporary distance cache used to as input for LOS calculation.
        dists_towers: MultiLookupDistanceCache = MultiLookupDistanceCache.from_distances(
            self.closest_towers())
        LOGGER.info(f"dists_towers: {len(dists_towers.lookup)}")

        # Final closest tower for each school.
        closest_visible_tower: List[PairwiseDistance] = []

        model = LineofSightModel()
        egp = ElevationProfileGenerator()
        for school_coord in self.school_coords:
            if school_coord.coordinate_id not in dists_towers.lookup:
                LOGGER.info(f"no towers for {school_coord.coordinate_id}")
                continue
            # Perform an LOS calculation to the closest N towers, then store
            # the closest with LOS.
            towers: List[PairwiseDistance] = dists_towers.lookup[school_coord.coordinate_id]
            coords = [[school_coord.coordinate, t.coordinate2.coordinate] for t in towers]
            los_results: List[bool] = model.run(egp.run(coords, samples=self.args.n_elevation_profile_samples))

            for tower, has_los in zip(towers, los_results):
                if not has_los:
                    continue
                closest_visible_tower.append(tower)
                LOGGER.info(f"found tower for {school_coord.coordinate_id}")
                break

        LOGGER.info("saving")
        # Save the final cache.
        p2p_cache = SingleLookupDistanceCache.from_distances(closest_visible_tower)
        p2p_cache.to_json(
            os.path.join(self.args.workspace_directory, f"p2p{self.args.file_suffix}.json")
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
    args: P2PCacheCreatorArgs = parser.parse_args()
    cache_creator = P2PCacheCreator(args)
    cache_creator.run()


if __name__ == "__main__":
    main()
