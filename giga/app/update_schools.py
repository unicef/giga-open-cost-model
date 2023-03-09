#!/usr/bin/env python3

import os
import argparse
import logging
import json
import math

from giga.utils.logging import LOGGER
import pandas as pd

from giga.data.web.giga_api_client import GigaAPIClient
from giga.schemas.school import GigaSchoolTable


def main():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("required arguments")
    required.add_argument("--workspace-directory", "-w", required=True)
    required.add_argument("--api-token", "-a", required=True)
    required.add_argument(
        "--country",
        "-c",
        choices=["sample", "rwanda", "brazil"],
        help="Specifies the country of interest, your workspace will need to contain the data for that country",
        required=True,
    )
    args = parser.parse_args()

    # export school data from project connect API
    client = GigaAPIClient(args.api_token)
    raw_schools = client.get_schools(args.country)

    # export electricity data and create a lookup
    el = pd.read_csv(os.path.join(args.workspace_directory, "electricity.csv"))
    electricity_lookup = {
        str(row.giga_id_school): bool(row.has_electricity) for i, row in el.iterrows()
    }

    def get_electricity_status(row):
        gid = str(row.giga_id)
        if gid in electricity_lookup:
            return electricity_lookup[gid]
        else:
            return False

    # trasnform raw school data
    table = GigaSchoolTable(schools=raw_schools)
    frame = table.to_data_frame()
    frame["connected"] = frame["connectivity_status"].apply(
        lambda x: True if (x == "Good" or x == "Moderate") else False
    )
    frame["has_electricity"] = frame.apply(get_electricity_status, axis=1)
    frame = frame.rename(
        columns={
            "giga_id": "giga_id_school",
            "school_zone": "environment",
            "connectivity_status": "connectivity_speed_status",
        }
    )

    # write to csv in the desired workspace
    frame.to_csv(os.path.join(args.workspace_directory, "schools.csv"), index=0)


if __name__ == "__main__":
    main()
