import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import math

from giga.viz.colors import (
    COST_COLORS_PAIR,
    COST_COLORS_TRIPLET,
    ORDERED_CUMULATIVE_DISTANCE_COLORS,
    SATELLITE_BREAKDOWN_COLORS,
    CELL_COVERAGE_COLOR_MAP,
    GIGA_TECHNOLOGY_COLORS
)


DEFAULT_FIBER_BINS = [0, 5_000, 10_000, 15_000, 20_000, np.inf]
DEFAULT_FIBER_NAMES = ["5km", "10km", "15km", "20km", "20km+"]

DEFAULT_CELL_BINS = [0, 1_000, 3_000, 5_000, 10_000, np.inf]
DEFAULT_CELL_NAMES = ["1km", "3km", "5km", "10km", "10km+"]

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


def technology_distribution_bar_plot(data):
    # data is a dictionary of technology counts
    # The data is in the form of {technology: count}
    total = sum(data.values())
    df = pd.DataFrame(list(data.items()), columns=["Technology", "Count"])
    # Calculate the percentage
    df["Percentage"] = np.round(df["Count"] / total * 100, 2)
    # Create the plot
    fig = go.Figure(
        data=[
            go.Bar(
                name="Count",
                x=df["Technology"],
                y=df["Count"],
                text=df["Count"],
                customdata=df["Percentage"],
                texttemplate="%{text}<br>%{customdata:.2f}%",
                textposition="outside",
                marker_color=["#009dff", "#59bfff", "#bfe6ff", "#e8ffff"],
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                opacity=0.6,
                width=[0.4] * len(df),
            )
        ]
    )
    # Update layout
    fig.update_layout(
        title=None,
        xaxis={
            "categoryorder": "total descending",
            "tickfont": dict(size=14, color="black", family="Arial, bold"),
            "range": [-0.5, len(df)],
        },
        yaxis=dict(title="", showticklabels=False, range=[0, max(df["Count"]) * 1.25]),
        bargap=0.3,
        plot_bgcolor="rgba(255, 255, 255, 1)",
        paper_bgcolor="rgba(255, 255, 255, 1)",
        shapes=[
            dict(
                type="line",
                yref="y",
                y0=0,
                y1=0,
                xref="x",
                x0=-0.5,
                x1=len(df) - 0.5,
                line=dict(color="Black", width=2),
            )
        ],
        autosize=True,
        margin=dict(t=0, r=100, l=20, b=0),
    )
    return fig


def make_cost_histogram(results, num_bins=40, cost_key="total_cost"):
    total_cost = results[cost_key].values

    # get colors based on bins
    colorscale = px.colors.diverging.RdYlGn[::-1][2:]
    color_min, color_max = np.min(total_cost), np.max(total_cost)
    bin_colors = np.linspace(color_min, color_max, num_bins + 1)
    fig = go.FigureWidget()
    # create histogram for each bin and assign color
    for i in range(num_bins):
        mask = (total_cost >= bin_colors[i]) & (total_cost < bin_colors[i + 1])
        color_index = int(
            np.interp(bin_colors[i], (color_min, color_max), (0, len(colorscale) - 1))
        )
        bin_data = total_cost[mask]
        bin_center = (bin_colors[i] + bin_colors[i + 1]) / 2  # calculate bin center
        fig.add_trace(
            go.Histogram(
                x=bin_data,
                marker_color=colorscale[color_index],
                hoverinfo="x+y",
                nbinsx=num_bins,
                name=f"{bin_colors[i]:.2f} - {bin_colors[i+1]:.2f}",
                showlegend=False,
            )
        )
        if len(bin_data) > 0:
            fig.add_trace(
                go.Scatter(
                    x=[bin_center],
                    y=[len(bin_data)],
                    mode="text",
                    text=[str(len(bin_data))],
                    textposition="top center",
                    textfont=dict(color="white", family="Arial"),
                    showlegend=False,
                )
            )
    # customize layout
    fig.update_layout(
        title_font_color="white",
        title={
            "text": "Cost Distribution",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                family="Arial",
                size=36,
                color="white",
            ),
        },
        barmode="stack",
        plot_bgcolor="#2a2a2a",
        paper_bgcolor="#2a2a2a",
        font=dict(color="white", family="Arial"),
        autosize=True,
        width=850,
        height=600,
        xaxis_title="Total Cost (USD)",
        yaxis=dict(showgrid=False, showticklabels=False),
        xaxis=dict(color="white", title_font=dict(color="white", family="Arial")),
        showlegend=False,
    )
    return fig


def cumulative_distance_bar_plot(
    data, distance_key, distance_cutoff, bins, names, title, x_label=None, y_label=None
):
    # Use the cut function
    df = data
    df["category"] = pd.cut(df[distance_key], bins, labels=names)
    # Convert the category to a categorical datatype and sort it based on the original order
    category_counts = df["category"].value_counts().sort_index()
    cumulative_counts = category_counts.cumsum()
    cumulative_counts = cumulative_counts.reindex(names, fill_value=0)
    # Sort cumulative_counts by the names list
    cumulative_counts = cumulative_counts[names]
    percent_within = round(sum(data[distance_key] <= distance_cutoff) / len(data) * 100)
    y_labels = [label + " " for label in cumulative_counts.index[::-1]]
    # Create the plot
    fig = go.Figure(
        data=[
            go.Bar(
                name="Count",
                x=list(cumulative_counts.values[::-1]),
                y=list(y_labels),
                text=list(cumulative_counts.values[::-1]),
                orientation="h",
                textposition="outside",
                marker_color=ORDERED_CUMULATIVE_DISTANCE_COLORS,
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                opacity=0.6,
                width=[0.4] * len(cumulative_counts),
            )
        ]
    )
    # Update layout
    fig.update_layout(
        title={
            "text": f"<b>{percent_within}% of " + title + "</b>",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                family="Arial",
                size=18,
                color="#000000",
            ),
        },
        bargap=0.3,
        plot_bgcolor="#faf8f2",
        paper_bgcolor="#faf8f2",
        yaxis={
            "title": y_label,
            "title_font": dict(size=15, color="black", family="Arial"),
            "categoryorder": "array",
            "tickfont": dict(size=13, color="black", family="Arial"),
            "range": [-0.5, len(cumulative_counts)],
        },
        xaxis={
            "title": x_label,
            "title_font": dict(size=15, color="black", family="Arial"),
            #"showticklabels": False,
            "showticklabels": True,
            "range": [0, max(cumulative_counts.values) * 1.1],
            #"title_standoff": 170,
        },
    )
    return fig


def cumulative_fiber_distance_barplot(
    data,
    distance_key="nearest_fiber",
    distance_cutoff=10_000,
    bins=DEFAULT_FIBER_BINS,
    names=DEFAULT_FIBER_NAMES,
    title="Unconnected Schools within 10km of a Fiber Node",
):
    return cumulative_distance_bar_plot(
        data, distance_key, distance_cutoff, bins, names, title,
        x_label="Number of schools within distance to a fiber node",
        y_label="Distance to node"
    )


def cumulative_cell_tower_distance_barplot(
    data,
    distance_key="nearest_cell_tower",
    distance_cutoff=3_000,
    bins=DEFAULT_CELL_BINS,
    names=DEFAULT_CELL_NAMES,
    title="Unconnected Schools within 3km of a Cell Tower",
):
    return cumulative_distance_bar_plot(
        data, distance_key, distance_cutoff, bins, names, title,
        x_label="Number of schools within distance to a cell tower",
        y_label="Distance to tower"
    )

def cumulative_visible_cell_tower_distance_barplot(
    data,
    distance_key="nearest_visible_cell_tower",
    distance_cutoff=3_000,
    bins=DEFAULT_CELL_BINS,
    names=DEFAULT_CELL_NAMES,
    title="Unconnected Schools within 3km of a Visible Cell Tower",
):
    return cumulative_distance_bar_plot(
        data, distance_key, distance_cutoff, bins, names, title,
        x_label="Number of schools within distance to a visible cell tower",
        y_label="Distance to visible tower"
    )

def make_project_cost_bar_plots(stats):
    totals_mil = stats.totals_lookup_table_mil
    df_totals = pd.DataFrame(zip(totals_mil.keys(), totals_mil.values()), columns= ['cost_type', 'cost'])

    fig = px.bar(
        df_totals,
        x='cost_type',
        y ='cost',
        color = 'cost_type',
        labels={
            "cost": "Cost (M USD)",
            "cost_type": "Cost Type",
        },
        #barmode="group",
        title='Total Project Costs (USD Millions)',
        color_discrete_sequence=COST_COLORS_TRIPLET,
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
    return fig


def make_unit_cost_bar_plot(stats):
    data = stats.unit_costs
    ORDERED_COST_COLORS = ["#d8e4e8", "#AFD3E2", "#19A7CE", "#146C94"]
    TECHNOLOGY_ORDER = ["Fiber", "P2P", "LEOs", "Cellular"]

    # Creating a categorical type for ordering
    cat_type = CategoricalDtype(categories=TECHNOLOGY_ORDER, ordered=True)

    fig = make_subplots(rows=1, cols=2)

    for idx, (cost_type, costs) in enumerate(data.items()):
        df = pd.DataFrame(
            [(k, v["cost"], v["label"]) for k, v in costs.items()],
            columns=["Type", "Cost", "Label"],
        )
        df["Type"] = df["Type"].astype(cat_type)
        df = df.sort_values("Type")
        max_value = df["Cost"].max()
        for i, row in df.iterrows():
            fig.add_trace(
                go.Bar(
                    name=row["Type"],
                    x=[row["Cost"]],
                    y=[row["Label"]],
                    marker_color=ORDERED_COST_COLORS[i],
                    text=[row["Cost"]],
                    textposition="auto",
                    orientation="h",
                    width=[0.5],
                    showlegend=False,
                ),
                row=1,
                col=idx + 1,
            )
        fig.update_yaxes(
            autorange="reversed", row=1, col=idx + 1
        )  # reverse y-axis to make 'Fiber' on top
        fig.update_xaxes(range=[0, max_value * 1.25], visible=False, row=1, col=idx + 1)

    fig.update_layout(
        barmode="group",
        plot_bgcolor="white",
        yaxis=dict(automargin=True),
        yaxis2=dict(automargin=True),
        width=1000,
        height=600,
        autosize=False,
        title={
            'text': "Upfront cost by Technology (USD) &nbsp;&nbsp;&nbsp;  &nbsp;&nbsp;&nbsp; Ongoing Costs ($/Mbps a year)",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family="Arial",
                size=18,
                color="black"
            )
        }
    )
    return fig


def make_satellite_pie_breakdown(to_show):
    # Create a new column to classify technologies as "Satellite" or "Other"
    to_show["tech_class"] = to_show["technology"].apply(
        lambda x: "Satellite" if x == "Satellite" else "Other"
    )
    # Get the count for each class
    grouped = to_show["tech_class"].value_counts().reset_index()
    grouped.columns = ["tech_class", "total"]
    # Calculate the percentage for each class
    grouped["percentage"] = (grouped["total"] / grouped["total"].sum()) * 100

    # Create a pie chart
    # Create a Pie chart using plotly.graph_objects.Pie  
    fig = go.Figure(  
        go.Pie(  
            labels=grouped["tech_class"],  
            values=grouped["total"],  
            text=grouped["tech_class"],  
            insidetextorientation='radial',  # Adjust text orientation  
            textposition='inside',  # Position text inside the pie slices  
            marker=dict(colors=list(SATELLITE_BREAKDOWN_COLORS.values())),
            #color_discrete_map=SATELLITE_BREAKDOWN_COLORS,
            textinfo="value+percent",  # Display labels, values, and percentages  
            hoverinfo="value+percent",  # Display hover information  
        )  
    ) 
    # Show the total counts and percentages on the plot
    #fig.update_traces(textinfo="label+value+percent", hoverinfo="label+value+percent")
    # Add title to the plot
    fig.update_layout(
        title={
            "text": "<b>Satellite Only Viable Modality</b>",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=24, color="black", family="Arial"),
        },
        showlegend=False,
        margin=dict(t=100),
    )  # Adjust top margin to fit title)
    return fig

def make_tech_pie_chart(df):
    # Calculate value counts and percentages
    value_counts = df['type_connectivity'].value_counts()
    percentages = (value_counts / value_counts.sum()) * 100
    
    #Let's remove small percentages otherwise it plots ugly
    mask = percentages < 1
    mask['Other'] = False
    # Compute the sum of these values
    sum_others = percentages[mask].sum()

    # Drop these entries from the series
    percentages = percentages[~mask]

    # Add a new entry "others"
    if 'Other' in percentages:
        percentages['Other'] += sum_others
    else:
        percentages['Other'] = sum_others

    # Create a Pie chart using plotly.graph_objects.Pie
    fig = go.Figure(
        go.Pie(
            labels=percentages.index,
            values=percentages.values,
            textinfo="percent",  
            hoverinfo="percent", 
            marker = dict(colors=percentages.index.map(GIGA_TECHNOLOGY_COLORS).fillna("#000000")),
            insidetextorientation='radial',  # Adjust text orientation  
            textposition='inside',  # Position text inside the pie slices 
        )
    )
    # Add title to the plot
    fig.update_layout(
        title={
            "text": "<b>Current technology distribution</b>",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=24, color="black", family="Arial"),
        },
        showlegend=True,
        margin=dict(t=100),
    )  # Adjust top margin to fit title)
    return fig

def make_coverage_bar_plot(arr: np.array):

    unique_elements, counts = np.unique(arr, return_counts=True)

    # Calculate cumulative distribution
    counts_percentage = counts / np.sum(counts) * 100 

    sorted_indices = np.argsort(counts)[::-1]  
    sorted_elements = unique_elements[sorted_indices]  
    sorted_counts = counts[sorted_indices]
    sorted_counts_percentage = counts_percentage[sorted_indices]  

    colors = [CELL_COVERAGE_COLOR_MAP.get(element, "#000000") for element in sorted_elements]

    fig = go.FigureWidget()

    fig.add_trace(
        go.Bar(  
            x=sorted_counts,
            y=sorted_elements,
            orientation="h",  
            marker=dict(color=colors),  
            text=np.round(sorted_counts_percentage, 2),
            texttemplate="%{text:.2f}%",  
            textposition="outside",  
            name="",
            opacity=0.6,
            width=[0.4] * len(sorted_elements),
        )
    )

    fig.update_layout(
        title={
            'text': f'<b>Distribution of Coverage Type</b>',
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                family="Arial",
                size=18,
                color="#000000",
            ),
        },
        xaxis={
            "title_font": dict(size=15, color="black", family="Arial"),
            "showticklabels": True,
            "range": [0, max(sorted_counts) * 1.1],
            'title': "Count",
        },
        yaxis={
            'title': "Coverage type",
            "title_font": dict(size=15, color="black", family="Arial"),
            "categoryorder": "array",
            "tickfont": dict(size=13, color="black", family="Arial"),
            "range": [-0.5, len(sorted_counts)],
        },
        bargap=0.3,
        plot_bgcolor="#faf8f2",
        paper_bgcolor="#faf8f2",
    )

    return fig


def make_results_tech_pie(new_connected_schools):

    technology_counts = new_connected_schools["technology"].value_counts().reset_index()  
    technology_counts.columns = ["technology", "count"]
    
    fig = go.FigureWidget()

    fig.add_trace(
        go.Pie(
            labels=new_connected_schools['technology'],
            values=technology_counts["count"],
            marker=dict(colors=technology_counts["technology"].map(GIGA_TECHNOLOGY_COLORS)),  
            textinfo="value+percent",  
            hoverinfo="value+percent", 
            insidetextorientation='radial',  # Adjust text orientation  
            textposition='inside',  # Position text inside the pie slices 
        )
    )

    # Add title to the plot
    fig.update_layout(
        title={
            "text": "<b>Number of Newly Schools Connected by Technology Type</b>",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=24, color="black", family="Arial"),
        },
        showlegend=True,
        margin=dict(t=100),
    )  # Adjust top margin to fit title)

    return fig