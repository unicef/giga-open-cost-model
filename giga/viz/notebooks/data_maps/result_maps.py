import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


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


def make_cost_map(results):
    to_show = results[results['feasible']]
    map_costs = px.density_mapbox(
        to_show,
        lat="lat",
        lon="lon",
        z="total_cost",
        radius=8,
        color_continuous_scale=px.colors.diverging.RdYlGn[
            ::-1
        ],  # Invert the RdYlGn scale for green-to-red
        hover_name="school_id",
        hover_data=["technology"],
        zoom=6,
        height=500,
        width=850,
        opacity=0.85,
        mapbox_style="carto-darkmatter",
    )
    map_costs.update_layout(
        coloraxis_colorbar=dict(
            x=0.02,
            y=0.5,
            title="Cost (USD)",
            titlefont=dict(size=14, family="Arial, sans-serif", color="#f5f5f5"),
            tickfont=dict(size=12, family="Arial, sans-serif", color="#f5f5f5"),
            bgcolor="rgba(0, 0, 0, 0.3)",
        )
    )
    return map_costs


def make_technology_map(results):
    to_show = results[results['feasible']]
    map_technology = px.scatter_mapbox(
        to_show,
        lat="lat",
        lon="lon",
        color="technology",
        hover_name="school_id",
        hover_data=["technology", "total_cost"],
        zoom=6,
        color_discrete_map={
            "Cellular": "#edece6",
            "Satellite": "#277aff",
            "P2P": "#46c66d",
            "Fiber": "#ff9f40",
        },
        height=500,
        width=850,
        mapbox_style="carto-darkmatter",
    )
    map_technology.update_layout(
        legend=dict(
            title="Technology",
            x=0.02,
            y=0.98,
            # titlefont=dict(size=14, family="Arial, sans-serif"),
            font=dict(size=12, family="Arial, sans-serif", color="white"),
            bgcolor="#242423",
            bordercolor="black",
            borderwidth=1,
        ),
    )
    return map_technology


def make_technology_average_cost_barplot(df):
    df_agg = (
        df.groupby("technology")
        .agg({"capex_total": "mean", "opex_total": "mean", "total_cost": "mean"})
        .reset_index()
    )
    df_agg = df_agg.append(
        pd.DataFrame(
            [
                {
                    "technology": "All",
                    "capex_total": df_agg.mean()["capex_total"],
                    "opex_total": df_agg.mean()["opex_total"],
                    "total_cost": df_agg.mean()["total_cost"],
                }
            ]
        )
    )

    fig = px.bar(
        df_agg,
        x="technology",
        y=["capex_total", "opex_total", "total_cost"],
        labels={
            "value": "Cost (USD)",
            "variable": "Cost Type",
            "technology": "Technology",
        },
        barmode="group",
        title="Average Costs by Technology",
        color_discrete_sequence=["#E3D8F1", "#BF8B85", "#5D5F71"],
        facet_row_spacing=0.1,
        template=CUSTOM_TEMPLATE,
    )

    # Clean up the background and change the font
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="#f5f5f5",
        title=dict(x=0.5, font=dict(size=16, family="Arial, sans-serif")),
        font=dict(size=14, family="Arial, sans-serif"),
        bargap=0.8,
        width=1200,
    )
    fig.for_each_trace(
        lambda trace: trace.update(
            name=trace.name.replace("capex_total", "CapEx")
            .replace("opex_total", "OpEx")
            .replace("total_cost", "Total Cost")
        )
    )
    return fig


def make_technology_total_cost_barplot(df):
    df_agg = (
        df.groupby("technology")
        .agg({"capex_total": "sum", "opex_total": "sum", "total_cost": "sum"})
        .reset_index()
    )
    df_agg = df_agg.append(
        pd.DataFrame(
            [
                {
                    "technology": "All",
                    "capex_total": df_agg.sum()["capex_total"],
                    "opex_total": df_agg.sum()["opex_total"],
                    "total_cost": df_agg.sum()["total_cost"],
                }
            ]
        )
    )

    fig = px.bar(
        df_agg,
        x="technology",
        y=["capex_total", "opex_total", "total_cost"],
        labels={
            "value": "Cost (USD)",
            "variable": "Cost Type",
            "technology": "Technology",
        },
        barmode="group",
        title="Total Costs by Technology",
        color_discrete_sequence=["#E3D8F1", "#BF8B85", "#5D5F71"],
        facet_row_spacing=0.1,
        template=CUSTOM_TEMPLATE,
    )

    # Clean up the background and change the font
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="#f5f5f5",
        title=dict(x=0.5, font=dict(size=16, family="Arial, sans-serif")),
        font=dict(size=14, family="Arial, sans-serif"),
        bargap=0.8,
        width=1200,
    )
    fig.for_each_trace(
        lambda trace: trace.update(
            name=trace.name.replace("capex_total", "CapEx")
            .replace("opex_total", "OpEx")
            .replace("total_cost", "Total Cost")
        )
    )
    return fig
