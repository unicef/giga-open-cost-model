import ipywidgets as widgets
import plotly.graph_objects as go
from IPython.display import display
import plotly.express as px

from giga.viz.notebooks.data_maps.result_maps import (
    make_cost_map,
    make_technology_map,
    make_technology_average_cost_barplot,
    make_technology_total_cost_barplot,
)
from giga.viz.notebooks.components.html.sections import section


class ResultDashboard:
    def __init__(self, results, height=650):
        self.results = results
        self.height = height

    def display(self):
        tabs = widgets.Tab(
            children=[self.maps_tab(), self.cost_tab(), self.technology_tab()]
        )
        tabs.set_title(0, "Maps")
        tabs.set_title(1, "Cost")
        tabs.set_title(2, "Technology")

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
        </style>
        """

        display(widgets.HTML(style))
        display(tabs)

    def _update_title_font(self, fig):
        fig.update_layout(
            title_font=dict(family="Arial, sans-serif", size=14, color="black")
        )

    def _figure_to_output(self, fig, layout=widgets.Layout(width="100%")):
        self._update_title_font(fig)
        output = widgets.Output(layout=layout)
        with output:
            display(fig)
        return output

    def maps_tab(self):
        map_costs = self._figure_to_output(make_cost_map(self.results))
        map_technology = self._figure_to_output(make_technology_map(self.results))

        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Connectivity Costs Map", map_costs, "dark"),
                        section("Connectivity Technology Map", map_technology, "dark"),
                    ]
                )
            )
        return tab

    def cost_tab(self):
        average_cost_barplot = make_technology_average_cost_barplot(self.results)
        total_cost_barplot = make_technology_total_cost_barplot(self.results)

        average_cost_output = self._figure_to_output(average_cost_barplot)
        total_cost_output = self._figure_to_output(total_cost_barplot)

        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Average Cost", average_cost_output),
                        section("Total Cost", total_cost_output),
                    ]
                )
            )
        return tab

    def technology_tab(self):
        to_show = self.results[self.results['feasible']]
        technology_pie = self._figure_to_output(
            px.pie(to_show, names="technology")
        )
        cost_pie = self._figure_to_output(
            px.pie(to_show, values="total_cost", names="technology")
        )
        feasibility_pie = self._figure_to_output(px.pie(self.results, names="reason"))

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
