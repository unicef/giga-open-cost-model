#!/usr/bin/env python3

import os
import argparse
from glob import glob
from os.path import join, getctime
import pandas as pd
from tqdm import tqdm

import warnings

warnings.filterwarnings("ignore")


CELL_TOWER_PRIMARY_KEY = "NumEstacao"


def get_sort_files(path, extension):
    list_of_files = []
    for file in glob(join(path, f"*{extension}")):
        list_of_files.append((getctime(file), file))
    return [file for _, file in sorted(list_of_files)]


def drop_duplicates(frame, primary_key):
    return frame.drop_duplicates(subset=primary_key, keep="last")


def main():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("required arguments")
    required.add_argument("--input-workspace", "-i", required=True)
    required.add_argument("--output-file", "-o", required=True)
    args = parser.parse_args()

    cell_towers_raw = pd.DataFrame()
    table_files = get_sort_files(args.input_workspace, "csv")
    for f in tqdm(table_files):
        df = pd.read_csv(f, encoding="iso-8859-1")
        df = drop_duplicates(df, CELL_TOWER_PRIMARY_KEY)
        cell_towers_raw = pd.concat([cell_towers_raw, df])
    cell_towers_raw = drop_duplicates(cell_towers_raw, CELL_TOWER_PRIMARY_KEY)

    # re-name and drop irrelevant columns
    cell_towers_raw = cell_towers_raw.rename(
        columns={
            "NumEstacao": "Site ID",
            "AlturaAntena": "Tower Height",
            "Tecnologia": "Technology",
        }
    )
    # placeholders below
    cell_towers_raw["Ownership of site"] = "Unknown"
    cell_towers_raw["Indoor /outdoor"] = "Outdoor"
    cell_towers_raw["Technology"] = "LTE"
    # keep only the relevant columns
    cell_towers_raw = cell_towers_raw[
        [
            "Site ID",
            "Ownership of site",
            "Indoor /outdoor",
            "Latitude",
            "Longitude",
            "Tower Height",
            "Technology",
        ]
    ]
    cell_towers_raw = cell_towers_raw.dropna(subset=["Latitude", "Longitude"])
    cell_towers_raw.to_csv(args.output_file, index=False)


if __name__ == "__main__":
    main()
