#!/usr/bin/env python3

import os
import argparse
import logging
import math

from giga.utils.logging import LOGGER
import pandas as pd

from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.school import GigaSchoolTable
from giga.schemas.cellular import CellTowerTable
from giga.schemas.geo import UniqueCoordinateTable
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.schemas.distance_cache import (
    SingleLookupDistanceCache,
    MultiLookupDistanceCache,
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
    args = parser.parse_args()

    cellular_coordinates = CellTowerTable.from_csv(
        os.path.join(args.workspace_directory, "cellular.csv")
    )
    school_coords = GigaSchoolTable.from_csv(
        os.path.join(args.workspace_directory, "schools.csv")
    )

    model = VectorizedDistanceModel(
        progress_bar=True,
        n_nearest_neighbors=args.n_nearest_neighbors,
        maximum_distance=args.maximum_distance_meters,
    )
    dists_cellular = model.run_chunks(
        (school_coords.to_coordinates(), cellular_coordinates.to_coordinates()),
        n_chunks=args.n_chunks,
    )
    cellular_cache = SingleLookupDistanceCache.from_distances(dists_cellular)
    cellular_cache.to_json(
        os.path.join(args.workspace_directory, f"cellular{args.file_suffix}.json")
    )


if __name__ == "__main__":
    main()