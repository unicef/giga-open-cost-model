import os
import fnmatch
import json
from typing import List

from giga.utils.globals import COUNTRY_DEFAULT_WORKSPACE


def get_registered_countries(directory: str) -> None:
    countries = []
    for root, _, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, "*.json"):
            countries.append(filename.split(".")[0])
    return countries


def get_registered_country_names(default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE):
    countries = get_registered_countries(default_parameter_dir)
    return [c.replace("_", " ").title() for c in countries]


def get_country_defaults(
    workspace="workspace", default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE
):
    # NOTE: if the defaults need to be loaded from another data store you can reimplement
    # this function to pull from a known database or other data store
    countries = get_registered_countries(default_parameter_dir)
    defaults = {}
    for country in countries:
        with open(os.path.join(default_parameter_dir, f"{country}.json")) as f:
            default = json.load(f)
        default["data"]["workspace"] = workspace
        defaults[country] = default
    return defaults


def get_country_code_lookup(default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE):
    defaults = get_country_defaults(default_parameter_dir=default_parameter_dir)
    return {
        c: default["data"]["country_code"]
        for c, default in defaults.items()
        if default["data"]["country_code"]
    }
