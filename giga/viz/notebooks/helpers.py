import base64
import pandas as pd
import numpy as np
import math
from IPython.display import HTML


def download_link_frame(df, title="Download Results", filename="results.csv"):
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    html = html.format(payload=payload, title=title, filename=filename)
    return HTML(html)


def results_to_table(results, n_years=5, responsible_opex=None):
    df = pd.DataFrame(list(map(lambda x: dict(x), results)))
    if responsible_opex == "consumer":
        opex = df["opex_consumer"]
    elif responsible_opex == "provider":
        opex = df["opex_provider"]
    else:
        opex = df["opex"]
    df["total_cost"] = df["capex"] + opex * n_years
    df = df.replace(math.nan, np.nan).round(
        {"opex": 1, "opex_provider": 1, "opex_consumer": 1, "capex": 1, "total_cost": 1}
    )
    return df


def output_to_table(output_space, n_years=5, responsible_opex=None):
    if output_space.minimum_cost_result:
        results = output_space.minimum_cost_result
    else:
        results = output_space.technology_outputs[0].cost_results
    return results_to_table(results, n_years=n_years, responsible_opex=responsible_opex)


def results_to_aggregates(results, n_years=5, responsible_opex=None):
    df = results_to_table(
        results, n_years=n_years, responsible_opex=responsible_opex
    ).drop(columns=["school_id", "technology", "feasible", "reason"])
    dfm = pd.DataFrame([dict(df.mean())]).round(
        {"opex": 1, "opex_provider": 1, "opex_consumer": 1, "capex": 1, "total_cost": 1}
    )
    dfs = pd.DataFrame([dict(df.sum())]).round(
        {"opex": 1, "opex_provider": 1, "opex_consumer": 1, "capex": 1, "total_cost": 1}
    )
    return dfm, dfs


def output_summary(output_space):
    if output_space.minimum_cost_result:
        results = output_space.minimum_cost_result
    else:
        results = output_space.technology_outputs[0].cost_results
    return results_to_aggregates(results)
