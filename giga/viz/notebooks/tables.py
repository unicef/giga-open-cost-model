import pandas as pd
import numpy as np
from ipywidgets import interactive, IntRangeSlider, Layout, HTML
from IPython.display import display
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from babel.numbers import format_currency
import seaborn as sns

from giga.viz.notebooks.helpers import output_to_table

mpl.rcParams["figure.dpi"] = 250


def output_to_school_stats(output_table):
    dfs = pd.DataFrame(
        [
            {
                "Number of Schools": len(output_table),
                "Schools that can be connected": sum(output_table["feasible"]),
                "Schools requiring electricity": len(
                    output_table[output_table["capex_electricity"] > 0.0]
                ),
            }
        ]
    )
    return dfs.transpose()


def output_to_technology_stats(output_table):
    feasible = output_table[output_table["feasible"]]
    return pd.DataFrame(feasible["technology"].value_counts())


def output_to_capex_details(output_table):
    df_means = (
        output_table.rename(columns={"capex_technology": "Per School"})
        .groupby("technology")
        .mean()["Per School"]
    )
    df_sums = (
        output_table.rename(columns={"capex_technology": "Total Costs"})
        .groupby("technology")
        .sum()["Total Costs"]
    )
    dfcap = pd.DataFrame([df_means, df_sums])
    dfcap = dfcap.transpose().round(decimals=0)
    dfcap.index = dfcap.index.rename("")
    return dfcap


def output_to_electricity_capex(output_table):
    per_school_solar = np.mean(
        output_table[output_table["capex_electricity"] > 0]["capex_electricity"]
    )
    if per_school_solar is np.nan:
        per_school_solar = 0.0
    total_solar = sum(
        output_table[output_table["capex_electricity"] > 0]["capex_electricity"]
    )
    return (
        pd.DataFrame(
            [
                {
                    "Number Schools Requiring Solar": len(
                        output_table[output_table["capex_electricity"] > 0.0]
                    ),
                    "Per School Solar Panel Costs": value_to_dollar_format(
                        per_school_solar
                    ),
                    "Total Solar Costs": value_to_dollar_format(total_solar),
                }
            ]
        )
        .transpose()
        .style.hide_columns()
    )


def output_to_opex_details(output_table):
    output_table["School Per Month"] = output_table["opex_connectivity"] / 12.0
    output_table["Electricity Per Month"] = output_table["opex_electricity"] / 12.0
    output_table["Total Annual per School Cost"] = (
        output_table["opex_connectivity"] + output_table["opex_electricity"]
    )
    output_table["Total Annual per Provider Cost"] = output_table["opex_technology"]

    df_means_month = output_table.groupby("technology").mean()["School Per Month"]
    df_means_year = output_table.groupby("technology").sum()["opex_connectivity"]

    dfop = pd.DataFrame([df_means_month, df_means_year]).round(decimals=0)
    dfop["Electricity Costs"] = [
        output_table["opex_electricity"].mean() / 12.0,
        output_table["opex_electricity"].sum(),
    ]
    dfop = dfop.transpose().round(decimals=0)
    dfop.index = dfop.index.rename("")
    dfop = dfop.rename(columns={"opex_connectivity": "Total Annual Cost"})
    return dfop


def value_to_dollar_format(val):
    return format_currency(val, currency="USD", locale="en_US")


def format_dollars(df, columns):
    for c in columns:
        df[c] = df[c].apply(
            lambda x: format_currency(x, currency="USD", locale="en_US")
        )
    return df


def display_summary_table(output_space):
    def get_space(t, num):
        s = ""
        for _ in range(num):
            s += t
        return s

    output_table = output_to_table(output_space)
    dfs = output_to_school_stats(output_table)
    dft = output_to_technology_stats(output_table)
    dfcap = output_to_capex_details(output_table)
    df_solar = output_to_electricity_capex(output_table)
    dfop = output_to_opex_details(output_table)

    cap_total = format_currency(
        sum(dfcap["Total Costs"]), currency="USD", locale="en_US"
    )
    op_total = format_currency(
        sum(dfop["Total Annual Cost"]), currency="USD", locale="en_US"
    )

    dfcap = format_dollars(dfcap, ["Per School", "Total Costs"])
    dfop = format_dollars(dfop, ["School Per Month", "Total Annual Cost"])

    display(
        HTML(value="<hr><hr><b><font color='#5b8ff0'>School Details</b><hr>"),
        dfs.style.hide_columns(),
    )
    display(
        HTML("<hr><b><font color='#5b8ff0'>Breakout by Technology</b><hr>"),
        dft.style.hide_columns(),
    )
    display(HTML("<hr><hr><b><font color='#5b8ff0'>CapEx Details</b><hr>"), dfcap)
    display(
        HTML(
            f"<b><font color='#50ba83'>Total CapEx Costs {get_space('&emsp;', 2)} {cap_total}</b><hr><hr>"
        )
    )
    display(HTML("<b><font color='#5b8ff0'>Electricity CapEx</b><hr>"), df_solar)
    display(HTML("<hr><hr><b><font color='#5b8ff0'>OpEx Details</b><hr>"), dfop)
    display(
        HTML(
            f"<b><font color='#50ba83'>Total OpEx Costs {get_space('&emsp;', 12)} {op_total}</b><hr><hr>"
        )
    )
    display(HTML("<b><font color='#5b8ff0'>Cost Breakdown</b>"))


def plot_cost_breakdown(output_space, data_space, border):
    def millions(x, pos):
        # The two args are the value and tick position
        return "%1.1fM" % (x * 1e-6)

    formatter = FuncFormatter(millions)

    output_table = output_to_table(output_space)
    schools = data_space.school_outputs_to_frame(output_table)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 5))

    border.to_crs(epsg=4326).plot(ax=ax1, color="lightgrey")
    schools.plot(
        column="total_cost",
        ax=ax1,
        cmap="rainbow",
        legend=True,
        legend_kwds={"shrink": 0.3},
        markersize=12,
    )
    ax1.set_title("Connectivity Cost Map")
    ax1.grid()

    s = schools[schools["feasible"]]
    labels = list(s["technology"].value_counts().index)
    data = list(s["technology"].value_counts())
    # define Seaborn color palette to use
    colors = sns.color_palette("pastel")[0 : len(data)]
    # create pie chart
    ax2.set_title("Breakdown by Technology")
    ax2.pie(data, labels=labels, colors=colors, autopct="%.0f%%")

    ax3.yaxis.set_major_formatter(formatter)
    sum_capex = sum(output_table["capex_total"].dropna())
    sum_opex = sum(output_table["opex_total"].dropna())
    barlist = ax3.bar(["One-Time CapEx", "Annual OpEx"], [sum_capex, sum_opex])
    b = barlist[0].set_color("#3258b8")
    b = barlist[1].set_color("#b54780")
    ax3.set_title("Total CapEx and OpEx")
    ax3.set_ylabel("USD")

    plt.show()


def apply_highlight(s, coldict):
    if s.name in coldict.keys():
        return ["background-color: {}".format(coldict[s.name])] * len(s)
    return [""] * len(s)


def interactive_cost_inspector_stats(
    df, columns_to_highlight=["capex", "opex", "total_cost"]
):
    coldict = {c: "#f2d591" for c in columns_to_highlight}

    def render(capex, opex, total_cost):
        filt = df[df["capex"].between(capex[0], capex[1])]
        filt = filt[filt["opex"].between(opex[0], opex[1])]
        filt = filt[filt["total_cost"].between(total_cost[0], total_cost[1])]
        if len(filt) > 0:
            display(filt.style.apply(apply_highlight, coldict=coldict))
        else:
            display(filt)

    capex_slider = IntRangeSlider(
        value=[0, 200_000],
        min=0,
        max=200_000,
        step=2_000,
        description="Capex:",
        layout=Layout(width="500px"),
    )
    opex_slider = IntRangeSlider(
        value=[0, 10_000],
        min=0,
        max=10_000,
        step=1_000,
        description="Opex:",
        layout=Layout(width="500px"),
    )

    total_cost_slider = IntRangeSlider(
        value=[0, 200_000],
        min=0,
        max=200_000,
        step=2_000,
        description="Total Cost:",
        layout=Layout(width="500px"),
    )

    interactive_plot = interactive(
        render, capex=capex_slider, opex=opex_slider, total_cost=total_cost_slider
    )

    for c in interactive_plot.children:
        c.style = {"description_width": "initial"}
    return interactive_plot
