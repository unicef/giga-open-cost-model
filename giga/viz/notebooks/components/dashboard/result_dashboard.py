import ipywidgets as widgets
import plotly.graph_objects as go
from IPython.display import display, Javascript
import plotly.express as px

from giga.viz.notebooks.data_maps.result_maps import (
    make_cost_map,
    make_technology_map,
    make_technology_average_cost_barplot,
    make_technology_total_cost_barplot,
    make_fiber_distance_map_plot,
    make_cellular_distance_map_plot,
    make_cellular_coverage_map,
)
from giga.viz.notebooks.tables import create_summary_table
from giga.viz.notebooks.components.charts.overview import (
    ProjectOverview,
    project_overview_grid,
)
from giga.viz.notebooks.components.html.sections import section
from giga.viz.notebooks.components.charts.plotters import (
    technology_distribution_bar_plot,
    cumulative_fiber_distance_barplot,
    cumulative_cell_tower_distance_barplot,
    make_cost_histogram,
    make_project_cost_bar_plots,
    make_unit_cost_bar_plot,
    make_satellite_pie_breakdown,
)
from giga.viz.colors import GIGA_TECHNOLOGY_COLORS
from giga.viz.plot_configs import STATIC_MAP_MODEBAR_CONFIG


class ResultDashboard:
    """
    Generates a dashboard for the results of a project.
    Displays the following in individual tabs:
    - Project Overview
    - Maps
    - Cost
    - Technology
    """

    def __init__(self, results, height=650):
        self.results = results
        self.height = height

    def display(self):
        tabs = widgets.Tab(
            children=[
                self.infrastructure_tab(),
                self.overview_tab(),
                self.cost_tab(),
                self.unit_cost_tab(),
            ]
        )
        tabs.set_title(0, "Infrastructure Availability")
        tabs.set_title(1, "Project Overview")
        tabs.set_title(2, "Project Cost")
        tabs.set_title(3, "Unit Costs")

        style = """
            <style>
                .widget-tab > .p-TabBar .p-TabBar-tab {
                    font-family: Arial, sans-serif;
                    font-weight: bold;
                    font-size: 14px;
                    background-color: lightgrey;
                    border-radius: 10px 10px 0 0;
                    padding: 5px;
                }
                .jupyter-widgets.widget-tab > .p-TabBar .p-TabBar-tab {
                    flex: 0 1 auto
                }
            </style>
        """
        display(widgets.HTML(style))
        display(tabs)

    def _update_title_font(self, fig):
        fig.update_layout(
            title_font=dict(family="Arial, sans-serif", size=16, color="black")
        )

    def _figure_to_output(self, fig, layout=widgets.Layout(width="100%")):
        self._update_title_font(fig)
        output = widgets.Output(layout=layout)
        with output:
            display(fig)
        return output

    def _map_to_output(self, fig, layout=widgets.Layout(width="850px", height="650px")):
        output = widgets.Output(layout=layout)
        fig = go.FigureWidget(fig)
        fig._config = {**fig._config, **STATIC_MAP_MODEBAR_CONFIG}
        with output:
            display(fig)
        return output

    def overview_tab(self):
        overview = self.results.output_project_overview
        overview_grid = project_overview_grid(overview)
        technology_distribution = self._figure_to_output(
            technology_distribution_bar_plot(self.results.technology_counts)
        )
        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.HBox(
                    [
                        section("Project Summary", overview_grid, "dark"),
                        section(
                            "Schools Connected by Technology",
                            technology_distribution,
                            "dark",
                        ),
                    ]
                )
            )
        return tab

    def infrastructure_tab(self):
        # Fiber Infra
        fiber_infra_map = self._map_to_output(
            make_fiber_distance_map_plot(self.results.new_connected_schools)
        )
        fiber_distance_bar = self._figure_to_output(
            cumulative_fiber_distance_barplot(self.results.output_cost_table)
        )
        fiber_plots = widgets.VBox([fiber_infra_map, fiber_distance_bar])
        # Cell Infra
        cell_infra_map = self._map_to_output(
            make_cellular_distance_map_plot(self.results.new_connected_schools)
        )
        cell_distance_bar = self._figure_to_output(
            cumulative_cell_tower_distance_barplot(self.results.output_cost_table)
        )
        cell_plots = widgets.VBox([cell_infra_map, cell_distance_bar])
        # Cell Coverage
        cell_coverage_map = self._map_to_output(
            make_cellular_coverage_map(self.results.new_connected_schools)
        )
        coverage_plots = widgets.VBox([cell_coverage_map])
        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        # Technology Map
        map_technology = self._map_to_output(
            make_technology_map(self.results.new_connected_schools)
        )
        # Satellite Breakdown
        satellite_breakdown = self._figure_to_output(
            make_satellite_pie_breakdown(self.results.new_connected_schools)
        )
        # cost maps
        map_costs = self._map_to_output(
            make_cost_map(
                self.results.new_connected_schools,
                cost_key="total_cost",
                display_key="Per School Cost (USD)",
                title="Average Cost Per School",
            )
        )
        map_costs_per_student = self._map_to_output(
            make_cost_map(
                self.results.new_connected_schools,
                cost_key="total_cost_per_student",
                display_key="Per Student Cost (USD)",
                title="Average Cost Per Student",
            )
        )
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Fiber Infrastructure", fiber_plots, "dark"),
                        section("Cellular Infrastructure", cell_plots, "dark"),
                        section("Cellular Coverage", coverage_plots, "dark"),
                        section("Technology Modalities", map_technology, "dark"),
                        section("Satellite Only Modality", satellite_breakdown, "dark"),
                        section("Average Cost Per School", map_costs, "dark"),
                        section(
                            "Average Cost Per Student", map_costs_per_student, "dark"
                        ),
                    ]
                )
            )
        return tab

    def maps_tab(self):
        # per school costs
        map_costs = self._figure_to_output(
            make_cost_map(self.results.new_connected_schools, cost_key="total_cost")
        )
        cost_dist = self._figure_to_output(
            make_cost_histogram(
                self.results.new_connected_schools, cost_key="total_cost"
            )
        )
        per_school_plots = widgets.VBox([map_costs])
        # per student costs
        map_costs_per_student = self._figure_to_output(
            make_cost_map(
                self.results.new_connected_schools, cost_key="total_cost_per_student"
            )
        )
        cost_dist_per_student = self._figure_to_output(
            make_cost_histogram(
                self.results.new_connected_schools, cost_key="total_cost_per_student"
            )
        )
        per_student_plots = widgets.VBox([map_costs_per_student])

        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.VBox(
                    [
                        section(
                            "Average Cost Per School", per_school_plots, "dark"
                        ).add_class("center"),
                        section(
                            "Average Cost Per Student", per_student_plots, "dark"
                        ).add_class("center"),
                    ]
                )
            )
        return tab

    def cost_tab(self):
        # project
        project_cost_barplot = self._figure_to_output(
            make_project_cost_bar_plots(self.results)
        )
        # averages
        average_cost_barplot = make_technology_average_cost_barplot(
            self.results.new_connected_schools
        )
        total_cost_barplot = make_technology_total_cost_barplot(
            self.results.new_connected_schools
        )
        # totals
        average_cost_output = self._figure_to_output(average_cost_barplot)
        total_cost_output = self._figure_to_output(total_cost_barplot)
        # pies
        to_show = self.results.new_connected_schools
        technology_pie = self._figure_to_output(
            px.pie(
                to_show,
                names="technology",
                color="technology",
                color_discrete_map=GIGA_TECHNOLOGY_COLORS,
            ).update_traces(
                textinfo="label+value+percent", hoverinfo="label+value+percent"
            )
        )
        cost_pie = self._figure_to_output(
            px.pie(
                to_show,
                values="total_cost",
                names="technology",
                color="technology",
                color_discrete_map=GIGA_TECHNOLOGY_COLORS,
            ).update_traces(
                textinfo="label+value+percent", hoverinfo="label+value+percent"
            )
        )
        # summary table
        summary_table = create_summary_table(
            self.results.output_space, self.results.data_space
        )

        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Project Costs", project_cost_barplot),
                        section(
                            "Average per School Technology Cost", average_cost_output
                        ),
                        section("Total Technology Costs", total_cost_output),
                        section(
                            "Number of Schools Connected by Tech Type", technology_pie
                        ),
                        section("Total CapEx and OpEx by Tech Type", cost_pie),
                        section(
                            "Total Costs by CapEx, OpEx, and Electricity", summary_table
                        ),
                    ]
                )
            )
        return tab

    def unit_cost_tab(self):
        unit_cost_plot = self._figure_to_output(make_unit_cost_bar_plot(self.results))
        tab = widgets.Output()
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Unit Cost", unit_cost_plot),
                    ]
                )
            )
        return tab

    def technology_tab(self):
        to_show = self.results.new_connected_schools
        technology_pie = self._figure_to_output(px.pie(to_show, names="technology"))
        cost_pie = self._figure_to_output(
            px.pie(to_show, values="total_cost", names="technology")
        )
        feasibility_pie = self._figure_to_output(
            px.pie(self.results.output_cost_table, names="reason")
        )

        tab = widgets.Output()
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Percent Technology", technology_pie),
                        section("Percent Cost", cost_pie),
                        section("Technology Feasibility", feasibility_pie),
                    ]
                )
            )
        return tab
