#!/usr/bin/env python3

import os
import argparse
import logging

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


def main():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "--country",
        "-c",
        choices=["sample", "rwanda", "brazil"],
        help="Specifies the country of interest, your workspace will need to contain the data for that country",
        required=True,
    )
    required.add_argument("--workspace-directory", "-w", required=True)
    optional = parser.add_argument_group("optional arguments")
    args = parser.parse_args()

    fiber_coordinates = UniqueCoordinateTable.from_csv(
        os.path.join(args.workspace_directory, f"{args.country}/fiber.csv")
    )
    school_coords = GigaSchoolTable.from_csv(
        os.path.join(args.workspace_directory, f"{args.country}/schools.csv")
    )

    model = VectorizedDistanceModel(progress_bar=True, n_nearest_neighbors=15)
    dists_fiber = model.run(
        (school_coords.to_coordinates(), fiber_coordinates.coordinates)
    )
    fiber_cache = SingleLookupDistanceCache.from_distances(dists_fiber)
    fiber_cache.to_json(
        os.path.join(args.workspace_directory, f"{args.country}/fiber_cache.json")
    )

    model = VectorizedDistanceModel(progress_bar=True, n_nearest_neighbors=15)
    dists_schools = model.run_chunks(
        (school_coords.to_coordinates(), school_coords.to_coordinates())
    )
    school_cache = MultiLookupDistanceCache.from_distances(dists_schools)
    school_cache.to_json(
        os.path.join(args.workspace_directory, f"{args.country}/school_cache.json")
    )


if __name__ == "__main__":
    main()
