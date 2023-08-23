import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from giga.viz.colors import (
    ORDERED_COST_COLORS,
    GIGA_TECHNOLOGY_COLORS,
    FIBER_COLORBAR_MIN,
    FIBER_COLORBAR_MAX,
    CELLULAR_COLORBAR_MIN,
    CELLULAR_COLORBAR_MAX,
    GIGA_BLACK,
    GIGA_WHITE,
    CELL_COVERAGE_COLOR_MAP,
)

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
    results, cost_key="total_cost", display_key="Total Cost (USD)", title="Cost Map"
):
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
        legend=dict(
            title="Technology",
            x=0.0,
            y=1.0,
            font=dict(size=12, family="Arial", color="white"),
            bgcolor="#242423",
            bordercolor="black",
            borderwidth=1,
        ),
    )
    map_technology.layout.title = {
        "text": "<b>Unconnected Schools - Modality to Connect</b>",
        "y": 0.96,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
        "font": dict(
            size=18, color=GIGA_BLACK, family="Arial"
        ),  # customize font size here
    }
    return map_technology


def plot_pairwise_connections(connections, color="gold"):
    traces = []
    total_dist_km = np.round(sum([c.distance for c in connections]) / METERS_IN_KM, 2)
    title_html = f"Total length of connections: {total_dist_km} km"

    for c in connections:
        # Compute mid-point for hover information
        mid_lat = (c.coordinate1.coordinate[0] + c.coordinate2.coordinate[0]) / 2
        mid_lon = (c.coordinate1.coordinate[1] + c.coordinate2.coordinate[1]) / 2
        hover_text = f"Distance: {np.round(c.distance / METERS_IN_KM, 2)} km"

        # Create line trace
        line_trace = go.Scattermapbox(
            lat=[c.coordinate1.coordinate[0], c.coordinate2.coordinate[0], None],
            lon=[c.coordinate1.coordinate[1], c.coordinate2.coordinate[1], None],
            mode="lines",
            line=dict(width=2, color=color),
            hoverinfo="none",
            showlegend=False,
        )
        traces.append(line_trace)

        # Create mid-point trace for hover information
        mid_point_trace = go.Scattermapbox(
            lat=[mid_lat],
            lon=[mid_lon],
            mode="markers",
            marker=dict(size=0),  # Invisible marker
            text=[hover_text],
            hoverinfo="text",
            showlegend=False,
            hoverlabel=dict(
                bgcolor="darkgray",  # Set background color
                font=dict(color="white", family="Arial"),  # Set font color
            ),
        )
        traces.append(mid_point_trace)

    return traces, title_html


def create_fiber_nodes_trace(fiber_nodes, color="black"):
    latitudes = [node.coordinate[0] for node in fiber_nodes]
    longitudes = [node.coordinate[1] for node in fiber_nodes]
    fiber_nodes_trace = go.Scattermapbox(
        lat=latitudes,
        lon=longitudes,
        mode="markers",
        marker=dict(size=8, color=color),  # Adjust size and color as needed
        text=[node.coordinate_id for node in fiber_nodes],
        hoverinfo="text",
        name="Fiber Nodes",  # This will appear in the legend
    )
    return fiber_nodes_trace


def make_technology_map_with_fiber(stats, style="carto-positron"):
    map_technology = make_technology_map(stats.new_connected_schools, style=style)
    lines, title_html = plot_pairwise_connections(stats.fiber_connections)
    for line in lines:
        map_technology.add_trace(line)
    fiber_nodes_trace = create_fiber_nodes_trace(stats.data_space.fiber_coordinates)
    map_technology.add_trace(fiber_nodes_trace)
    map_technology.layout.title.text = title_html
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


def make_fiber_distance_map_plot(
    results, distance_lower=FIBER_COLORBAR_MIN, distance_upper=FIBER_COLORBAR_MAX
):
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
        range_color=[distance_lower, distance_upper],
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
            title=dict(font=dict(color="#474747", family="Arial")), tickfont=dict(color="#474747", family="Arial")
        )
    )
    fig.layout.title = {
        "text": "<b>Unconnected School Proximity to Fiber Nodes</b>",
        "y": 0.96,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
        "font": dict(
            size=18, color=GIGA_BLACK, family="Arial"
        ),  # customize font size here
    }
    return go.FigureWidget(fig)


def make_cellular_distance_map_plot(
    results, distance_lower=CELLULAR_COLORBAR_MIN, distance_upper=CELLULAR_COLORBAR_MAX
):
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
        range_color=[distance_lower, distance_upper],
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
        title={
            "text": "<b>Unconnected School Proximity to Cell Towers</b>",
            "y": 0.96,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                size=18, color=GIGA_BLACK, family="Arial"
            ),  # customize font size here
        },
    )
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(font=dict(color="#474747", family="Arial")), tickfont=dict(color="#474747", family="Arial")
        )
    )
    return fig

def make_p2p_distance_map_plot(
    results, distance_lower=CELLULAR_COLORBAR_MIN, distance_upper=CELLULAR_COLORBAR_MAX
):
    style = "carto-positron"
    df = results.rename(columns={"nearest_visible_cell_tower": "Nearest Visible Cell Tower (km)"})
    df["Nearest Visible Cell Tower (km)"] = np.round(df["Nearest Visible Cell Tower (km)"] / 1_000, 2)
    df["size"] = np.ones(len(df))
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        color="Nearest Visible Cell Tower (km)",
        color_continuous_scale="Bluered",
        size="size",
        zoom=7,
        size_max=3,
        mapbox_style=style,
        range_color=[distance_lower, distance_upper],
        hover_data={
            "lat": False,
            "lon": False,
            "size": False,
            "school_id": True,
            "Nearest Visible Cell Tower (km)": True,
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
        title={
            "text": "<b>Unconnected School Proximity to Visible Cell Towers</b>",
            "y": 0.96,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                size=18, color=GIGA_BLACK, family="Arial"
            ),  # customize font size here
        },
    )
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(font=dict(color="#474747", family="Arial")), tickfont=dict(color="#474747", family="Arial")
        )
    )
    return fig


def make_cellular_coverage_map(results, new_cell_key="Cell Coverage  "):
    categories_order = [
        t
        for t in list(reversed(CELL_COVERAGE_COLOR_MAP.keys()))
        if t in results["cell_coverage_type"].unique()
    ]
    df = results.rename(columns={"cell_coverage_type": new_cell_key})
    # Set order for categories
    df[new_cell_key] = pd.Categorical(
        df[new_cell_key], categories=categories_order, ordered=True
    )
    # Ensure all category levels are present in the data
    missing_categories = set(categories_order) - set(df[new_cell_key].unique())
    for category in missing_categories:
        df = df.append(
            {new_cell_key: category, "size": 0, "lat": np.nan, "lon": np.nan},
            ignore_index=True,
        )
    df["size"] = np.where(
        df[new_cell_key].isin(missing_categories), 0, np.ones(len(df))
    )
    style = "carto-positron"
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        color=new_cell_key,
        color_discrete_map=CELL_COVERAGE_COLOR_MAP,
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
            title=dict(font=dict(color="#474747", family="Arial")), tickfont=dict(color="#474747", family="Arial")
        )
    )
    fig.layout.title = {
        "text": "<b>Cellular Coverage</b>",
        "y": 0.96,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
        "font": dict(
            size=18, color=GIGA_BLACK, family="Arial"
        ),  # customize font size here
    }
    return fig
