import sys
import time
import base64
import pandas as pd
import numpy as np
import math
from IPython.display import display, clear_output
from ipywidgets import Button, Output
from giga.utils.logging import LOGGER


def run_message(wait_time=0.1):
    LOGGER.info("Run complete")


def results_to_table(results, n_years=5, responsible_opex=None):
    df = pd.DataFrame(list(map(lambda x: dict(x), results)))
    electricity_opex = list(
        map(
            lambda x: x.electricity.electricity_opex if x.feasible else math.nan,
            results,
        )
    )
    electricity_capex = list(
        map(
            lambda x: x.electricity.electricity_capex if x.feasible else math.nan,
            results,
        )
    )
    electricity_type = list(
        map(lambda x: x.electricity.cost_type if x.feasible else math.nan, results)
    )
    df["capex_technology"] = df["capex"]
    df["capex_electricity"] = electricity_capex
    df["opex_connectivity"] = df["opex_consumer"]
    df["opex_technology"] = df["opex_provider"]
    df["opex_electricity"] = electricity_opex
    df["capex_total"] = df["capex_technology"] + df["capex_electricity"]
    df["opex_total"] = (
        df["opex_connectivity"] + df["opex_technology"] + df["opex_electricity"]
    )
    df["total_cost"] = df["capex_total"] + df["opex_total"] * n_years
    df = df.drop(
        columns=["electricity", "opex_consumer", "opex_provider", "opex", "capex"]
    )
    df = df.replace(math.nan, np.nan).round(
        {
            "opex_total": 2,
            "opex_connectivity": 2,
            "opex_electricity": 2,
            "opex_technology": 2,
            "capex_total": 2,
            "capex_technology": 2,
            "capex_electricity": 2,
            "total_cost": 2,
        }
    )
    return df


def output_to_table(output_space, responsible_opex=None):

    if output_space.minimum_cost_result:
        results = output_space.minimum_cost_result
    else:
        if len(output_space.technology_outputs) == 0:
            # return an empty frame
            return pd.DataFrame()
        else:
            results = output_space.technology_outputs[0].cost_results
    return results_to_table(results, n_years=output_space.years_opex, responsible_opex=responsible_opex)


def results_to_aggregates(results, n_years=5, responsible_opex=None):
    df = results_to_table(
        results, n_years=n_years, responsible_opex=responsible_opex
    ).drop(columns=["school_id", "technology", "feasible", "reason"])
    df = df[["opex_total", "capex_total", "total_cost"]]
    dfm = pd.DataFrame([dict(df.mean())]).round(
        {"opex_total": 1, "capex_total": 1, "total_cost": 1}
    )
    dfs = pd.DataFrame([dict(df.sum())]).round(
        {"opex_total": 1, "capex_total": 1, "total_cost": 1}
    )
    return dfm, dfs


def output_summary(output_space):
    if output_space.minimum_cost_result:
        results = output_space.minimum_cost_result
    else:
        results = output_space.technology_outputs[0].cost_results
    return results_to_aggregates(results, n_years=output_space.years_opex)


def button_cb(description, action):
    b = Button(description=description)
    out = Output()
    display(b, out)

    def on_click(b):
        with out:
            clear_output(wait=True)
            action()

    return b, on_click
