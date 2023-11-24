import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


from giga.viz.colors import ORDERED_COST_COLORS

METERS_IN_KM = 1000.0


CUSTOM_TEMPLATE = custom_template = {
    "layout": go.Layout(
        font={
            "family": "Nunito",
            "size": 12,
            "color": "#707070",
        },
        title={
            "font": {
                "family": "Arial",
                "size": 18,
                "color": "#1f1f1f",
            },
        },
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        colorway=px.colors.qualitative.G10,
    )
}


def make_cost_map(
    results, country, cost_key="total_cost", display_key="Total Cost (USD)", title="Cost Map"):
    if country == 'BRA':
        zoom = 3
    else:
        zoom = 7
    df = results.rename(columns={cost_key: display_key})
    df["size"] = np.ones(len(df))
    style = "carto-darkmatter"
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        color=display_key,
        color_continuous_scale=px.colors.diverging.RdYlGn[::-1][2:],
        size="size",
        zoom=zoom,
        size_max=4,
        opacity=0.90,
        mapbox_style=style,
        hover_data={
            "lat": False,
            "lon": False,
            "size": False,
            "school_id": True,
            display_key: True,
        },
        width=850,
        height=650,
    )
    # Move colorbar to top left
    fig.update_layout(
        coloraxis_colorbar=dict(
            xanchor="left",
            yanchor="top",
            x=0.0,
            y=1.0,
        ),
        autosize=True,
        width=850,
        height=600,
    )
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(font=dict(color="#dbd5d5", family="Arial")), tickfont=dict(color="#dbd5d5", family="Arial")
        )
    )
    fig.layout.title = {
        "text": "<b style='color:white; background-color:black;'>" + title + "</b>",
        "y": 0.9,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
        "font": dict(
            size=18, color="white", family="Verdana"
        ),  # customize font size here
    }
    return fig


def make_technology_average_cost_barplot(
    df,
    capex_key="capex",
    capex_electricity_key="electricity_capex",
    opex_key="recurring_costs",
):
    df_agg = (
        df.groupby("technology")
        .agg(
            {
                capex_key: "mean",
                capex_electricity_key: "mean",
                opex_key: "mean",
                "total_cost": "mean",
            }
        )
        .reset_index()
    )
    df_agg = df_agg.append(
        pd.DataFrame(
            [
                {
                    "technology": "All",
                    capex_key: df_agg.mean()[capex_key],
                    capex_electricity_key: df_agg.mean()[capex_electricity_key],
                    opex_key: df_agg.mean()[opex_key],
                    "total_cost": df_agg.mean()["total_cost"],
                }
            ]
        )
    )

    fig = px.bar(
        df_agg,
        x="technology",
        y=[capex_key, capex_electricity_key, opex_key, "total_cost"],
        labels={
            "value": "Cost (USD)",
            "variable": "Cost Type",
            "technology": "Technology",
        },
        barmode="group",
        title="Average Costs by Technology",
        color_discrete_sequence=ORDERED_COST_COLORS,
        facet_row_spacing=0.2,
        template=CUSTOM_TEMPLATE,
    )

    # Clean up the background and change the font
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="#f5f5f5",
        title=dict(x=0.5, font=dict(size=18, family="Arial")),
        font=dict(size=14, family="Arial"),
        bargap=0.6,
        width=1200,
    )
    name_mapping = {
        capex_key: "CapEx Technology",
        capex_electricity_key: "CapEx Electricity",
        opex_key: "OpEx",
        "total_cost": "Total Cost",
    }

    fig.for_each_trace(
        lambda trace: trace.update(name=name_mapping.get(trace.name, trace.name))
    )
    return fig


def make_technology_total_cost_barplot(
    df,
    capex_key="capex",
    capex_electricity_key="electricity_capex",
    opex_key="recurring_costs",
):
    df_agg = (
        df.groupby("technology")
        .agg(
            {
                capex_key: "sum",
                capex_electricity_key: "sum",
                opex_key: "sum",
                "total_cost": "sum",
            }
        )
        .reset_index()
    )
    df_agg = df_agg.append(
        pd.DataFrame(
            [
                {
                    "technology": "All",
                    capex_key: df_agg.sum()[capex_key],
                    capex_electricity_key: df_agg.sum()[capex_electricity_key],
                    opex_key: df_agg.sum()[opex_key],
                    "total_cost": df_agg.sum()["total_cost"],
                }
            ]
        )
    )

    fig = px.bar(
        df_agg,
        x="technology",
        y=[capex_key, capex_electricity_key, opex_key, "total_cost"],
        labels={
            "value": "Cost (USD)",
            "variable": "Cost Type",
            "technology": "Technology",
        },
        barmode="group",
        title="Total Costs by Technology",
        color_discrete_sequence=ORDERED_COST_COLORS,
        facet_row_spacing=0.2,
        template=CUSTOM_TEMPLATE,
    )

    # Clean up the background and change the font
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="#f5f5f5",
        title=dict(x=0.5, font=dict(size=18, family="Arial")),
        font=dict(size=14, family="Arial"),
        bargap=0.6,
        width=1200,
    )
    name_mapping = {
        capex_key: "CapEx Technology",
        capex_electricity_key: "CapEx Electricity",
        opex_key: "OpEx",
        "total_cost": "Total Cost",
    }

    fig.for_each_trace(
        lambda trace: trace.update(name=name_mapping.get(trace.name, trace.name))
    )
    return fig
