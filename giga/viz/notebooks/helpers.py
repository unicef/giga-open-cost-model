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


def results_to_table(results, n_years=5):
    df = pd.DataFrame(list(map(lambda x: dict(x), results.cost_results)))
    df["total_cost"] = df["capex"] + df["opex"] * n_years
    df = df.replace(math.nan, np.nan).round({"opex": 1, "capex": 1, "total_cost": 1})
    # df['capex'], df['opex'], df['total_cost'] = df['capex'].astype('int'), df['opex'].astype('int'), df['total_cost'].astype('int')
    return df


def results_to_aggregates(results, n_years=5):
    df = results_to_table(results, n_years=n_years).drop(
        columns=["school_id", "technology", "feasible", "reason"]
    )
    dfm = pd.DataFrame([dict(df.mean())]).round(
        {"opex": 1, "capex": 1, "total_cost": 1}
    )
    dfs = pd.DataFrame([dict(df.sum())]).round({"opex": 1, "capex": 1, "total_cost": 1})
    return dfm, dfs
