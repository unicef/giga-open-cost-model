import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from jupyter_dash import JupyterDash
import plotly.express as px
from IPython import display

from giga.viz.notebooks.data_maps.result_maps import (
    make_cost_map,
    make_technology_map,
    make_technology_average_cost_barplot,
    make_technology_total_cost_barplot,
)
from giga.app.dashboard import find_dashboard_port


class DashDashboard:
    def __init__(self, height=650, theme=dbc.themes.CERULEAN):
        self.app = JupyterDash(__name__, external_stylesheets=[theme])
        self.port = find_dashboard_port()
        self.height = height

    def start_server(self):
        self.app.run_server(mode="external", height=f"{self.height}px", port=self.port)

    def maps_tab(self, results):
        map_costs = make_cost_map(results, title="Connectivity Costs Map")
        map_technology = make_technology_map(results)
        return dcc.Tab(
            label="Maps",
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1("Connectivity Costs Map"),
                                dcc.Graph(figure=map_costs),
                            ],
                            style={"flex": "1", "width": "50%"},
                        ),
                        html.Div(
                            [
                                html.H1("Connectivity Technology Map"),
                                dcc.Graph(figure=map_technology),
                            ],
                            style={"flex": "1", "width": "50%"},
                        ),
                    ],
                    style={"display": "flex", "height": "80vh"},
                ),
            ],
        )

    def cost_tab(self, results):
        average_cost_barplot = make_technology_average_cost_barplot(results)
        total_cost_barplot = make_technology_total_cost_barplot(results)
        return dcc.Tab(
            label="Cost",
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1("Average Cost"),
                                dcc.Graph(figure=average_cost_barplot),
                            ]
                        ),
                        html.Div(
                            [
                                html.H1("Total Cost"),
                                dcc.Graph(figure=total_cost_barplot),
                            ]
                        ),
                    ],
                    style={"height": "80vh"},
                ),
            ],
        )

    def technology_tab(self, results):
        technology_pie = px.pie(
            results, names="technology", title="Technology Distribution"
        )
        cost_pie = px.pie(
            results,
            values="total_cost",
            names="technology",
            title="Cost Distribution",
        )
        feasibility_pie = px.pie(results, names="reason", title="Feasibility Breakdown")
        return dcc.Tab(
            label="Technology",
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H1("Percent Technology"),
                                        dcc.Graph(figure=technology_pie),
                                    ],
                                    style={"flex": "1", "width": "50%"},
                                ),
                                html.Div(
                                    [
                                        html.H1("Percent Cost"),
                                        dcc.Graph(figure=cost_pie),
                                    ],
                                    style={"flex": "1", "width": "50%"},
                                ),
                            ],
                            style={"display": "flex"},
                        ),
                        html.Div(
                            [
                                html.H1("Technology Feasibility"),
                                dcc.Graph(
                                    figure=feasibility_pie
                                ),  # Replace with your actual figure
                            ],
                            style={"width": "100%", "marginTop": "2rem"},
                        ),
                    ],
                    style={"height": "80vh"},
                ),
            ],
        )

    @property
    def extra_tab(self, results):
        return dcc.Tab(
            label="Placeholder",
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1("Cost Breakdown by Technology"),
                                dcc.RadioItems(
                                    id="cost-toggle",
                                    options=[
                                        {"label": "Total", "value": "total"},
                                        {
                                            "label": "Consumer Costs",
                                            "value": "consumer",
                                        },
                                        {
                                            "label": "Provider Costs",
                                            "value": "provider",
                                        },
                                    ],
                                    value="total",
                                    inline=True,
                                ),
                                dcc.Graph(id="cost-breakdown"),
                            ]
                        ),
                    ],
                    style={"height": "80vh"},
                ),
            ],
        )

    def update_dashboard(self, results):
        self.app.layout = html.Div(
            [
                dcc.Tabs(
                    [
                        self.maps_tab(results),
                        self.cost_tab(results),
                        self.technology_tab(results),
                    ]
                ),
            ]
        )
        return self.app

    def display(self):
        display.display(
            display.IFrame(f"http://localhost:{self.port}", "100%", self.height)
        )
