#!/usr/bin/env python3

import os
import argparse
import logging
import json
import math

from giga.utils.logging import LOGGER
import pandas as pd

from giga.models.nodes.graph.greedy_distance_connector import GreedyDistanceConnector
from giga.schemas.school import GigaSchoolTable
from giga.schemas.geo import UniqueCoordinateTable
from giga.models.nodes.graph.vectorized_distance_model import VectorizedDistanceModel
from giga.schemas.distance_cache import (
    SingleLookupDistanceCache,
    MultiLookupDistanceCache,
)


def get_uncached_schools(schools, args, cache_file):
    if args.replace:
        return schools
    try:
        with open(os.path.join(args.workspace_directory, f"{cache_file}")) as f:
            cache = json.load(f)
        return schools.filter_schools_by_id(
            [sid for sid in table.school_ids if sid not in cache["lookup"]]
        )
    except FileNotFoundError:
        return schools


def main():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("required arguments")
    required.add_argument("--workspace-directory", "-w", required=True)
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "--replace",
        "-r",
        action="store_true",
        help="Specifies whether to fully replace the existing cache",
        default=False,
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

    fiber_coordinates = UniqueCoordinateTable.from_csv(
        os.path.join(args.workspace_directory, "fiber.csv")
    )
    school_coords = GigaSchoolTable.from_csv(
        os.path.join(args.workspace_directory, "schools.csv")
    )

    model = VectorizedDistanceModel(
        progress_bar=True,
        n_nearest_neighbors=args.n_nearest_neighbors,
        maximum_distance=args.maximum_distance_meters,
    )
    dists_fiber = model.run(
        (school_coords.to_coordinates(), fiber_coordinates.coordinates)
    )
    fiber_cache = SingleLookupDistanceCache.from_distances(dists_fiber)
    fiber_cache.to_json(
        os.path.join(args.workspace_directory, f"fiber{args.file_suffix}.json")
    )

    model = VectorizedDistanceModel(
        progress_bar=True,
        n_nearest_neighbors=args.n_nearest_neighbors,
        maximum_distance=args.maximum_distance_meters,
    )
    dists_schools = model.run_chunks(
        (school_coords.to_coordinates(), school_coords.to_coordinates())
    )
    school_cache = MultiLookupDistanceCache.from_distances(
        dists_schools, n_neighbors=args.n_nearest_neighbors
    )
    school_cache.to_json(
        os.path.join(args.workspace_directory, f"school{args.file_suffix}.json")
    )


if __name__ == "__main__":
    main()