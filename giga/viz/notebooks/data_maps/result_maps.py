import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from giga.viz.colors import ORDERED_COST_COLORS, GIGA_TECHNOLOGY_COLORS


CUSTOM_TEMPLATE = custom_template = {
    "layout": go.Layout(
        font={
            "family": "Nunito",
            "size": 12,
            "color": "#707070",
        },
        title={
            "font": {
                "family": "Lato",
                "size": 18,
                "color": "#1f1f1f",
            },
        },
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        colorway=px.colors.qualitative.G10,
    )
}


def make_cost_map(results, cost_key="total_cost", display_key="Total Cost (USD)"):
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
        zoom=7,
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
            title=dict(font=dict(color="#dbd5d5")), tickfont=dict(color="#dbd5d5")
        )
    )
    return fig


def make_technology_map(results, style="carto-positron"):
    map_technology = px.scatter_mapbox(
        results,
        title="Unconnected Schools",
        lat="lat",
        lon="lon",
        size=np.ones(len(results)),
        size_max=4,
        opacity=0.90,
        color="technology",
        hover_name="school_id",
        hover_data=["technology", "total_cost"],
        zoom=7,
        color_discrete_map=GIGA_TECHNOLOGY_COLORS,
        height=650,
        width=850,
        mapbox_style=style,
    )
    map_technology.update_layout(
        height=650,
        width=850,
        title={
            "text": "Your Title Here",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        title_font=dict(size=16, color="white", family="Arial, sans-serif"),
        legend=dict(
            title="Technology",
            x=0.0,
            y=1.0,
            # titlefont=dict(size=14, family="Arial, sans-serif"),
            font=dict(size=12, family="Arial, sans-serif", color="white"),
            bgcolor="#242423",
            bordercolor="black",
            borderwidth=1,
        ),
    )
    return map_technology


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
        title=dict(x=0.5, font=dict(size=16, family="Arial, sans-serif")),
        font=dict(size=14, family="Arial, sans-serif"),
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
        title=dict(x=0.5, font=dict(size=16, family="Arial, sans-serif")),
        font=dict(size=14, family="Arial, sans-serif"),
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


def make_fiber_distance_map_plot(results):
    style = "carto-positron"
    df = results.rename(columns={"nearest_fiber": "Nearest Fiber (km)"})
    df["Nearest Fiber (km)"] = np.round(df["Nearest Fiber (km)"] / 1_000, 2)
    df["size"] = np.ones(len(df))
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        color="Nearest Fiber (km)",
        color_continuous_scale="Bluered",
        size="size",
        zoom=7,
        size_max=3,
        mapbox_style=style,
        hover_data={
            "lat": False,
            "lon": False,
            "size": False,
            "school_id": True,
            "Nearest Fiber (km)": True,
        },
    )
    # Move colorbar to top left
    fig.update_layout(
        coloraxis_colorbar=dict(xanchor="left", yanchor="top", x=-0.4, y=1.2),
        width=850,
        height=650,
    )
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(font=dict(color="#474747")), tickfont=dict(color="#474747")
        )
    )
    return go.FigureWidget(fig)


def make_cellular_distance_map_plot(results):
    style = "carto-positron"
    df = results.rename(columns={"nearest_cell_tower": "Nearest Cell Tower (km)"})
    df["Nearest Cell Tower (km)"] = np.round(df["Nearest Cell Tower (km)"] / 1_000, 2)
    df["size"] = np.ones(len(df))
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        color="Nearest Cell Tower (km)",
        color_continuous_scale="Bluered",
        size="size",
        zoom=7,
        size_max=3,
        mapbox_style=style,
        hover_data={
            "lat": False,
            "lon": False,
            "size": False,
            "school_id": True,
            "Nearest Cell Tower (km)": True,
        },
    )
    # Move colorbar to top left
    fig.update_layout(
        coloraxis_colorbar=dict(
            xanchor="left",
            yanchor="top",
            x=-0.4,
            y=1.2,
        ),
        autosize=True,
        width=850,
        height=600,
    )
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(font=dict(color="#474747")), tickfont=dict(color="#474747")
        )
    )
    return fig


def make_cellular_coverage_map(results, new_cell_key="Cell Coverage  "):
    df = results.rename(columns={"cell_coverage_type": new_cell_key})
    df["size"] = np.ones(len(df))
    style = "carto-positron"
    color_discrete_map = {
        "None": "#e8ffff",
        "2G": "#bfe6ff",
        "3G": "#8cd3ff",
        "4G": "#009dff",
        "LTE": "#009dff",
    }  # Define color for each category here
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        color=new_cell_key,
        color_discrete_map=color_discrete_map,
        size="size",
        zoom=7,
        size_max=4,
        opacity=0.5,
        mapbox_style=style,
        hover_data={
            "lat": False,
            "lon": False,
            "size": False,
            "school_id": True,
            new_cell_key: True,
        },
    )
    # Move colorbar to top left
    fig.update_layout(
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.12),
        autosize=True,
        width=850,
        height=600,
    )
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(font=dict(color="#474747")), tickfont=dict(color="#474747")
        )
    )
    return fig
