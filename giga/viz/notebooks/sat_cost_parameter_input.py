from ipywidgets import (
    VBox,
    GridBox,
    Layout,
    HTML,
)

from giga.viz.notebooks.cost_estimation_parameter_input import (
    CostEstimationParameterInput,
)
from giga.viz.notebooks.parameters.groups.sat_scenario_parameter_manager import (
    SATScenarioParameterManager,
)
from giga.viz.notebooks.parameters.groups.sat_solver_parameter_manager import (
    SATSolverParameterManager,
)
import giga.viz.notebooks.components.html.sections as giga_sections


class SATCostParameterInput(CostEstimationParameterInput):
    def __init__(self, local_data_workspace="workspace", **kwargs):
        super().__init__(
            local_data_workspace=local_data_workspace,
            scenario_parameter_manager=SATScenarioParameterManager(),
            **kwargs
        )
        # create sat parameter manager
        self.sat_solver_parameter_manager = SATSolverParameterManager()
        # add to existing set of parameter managers to freeze/unfreeze at runtime
        self.managers["sat"] = [self.sat_solver_parameter_manager]

    def sat_parameters_input(self):
        return self.sat_solver_parameter_manager.input_parameters()

    def sat_parameters(self, sat_engine: bool = False, road_data: bool = False):
        return self.sat_solver_parameter_manager.get_model_parameters(
            sat_engine=sat_engine, road_data=road_data
        )

    def scenario_parameters(self):
        conf = super().scenario_parameters()
        p = self.scenario_parameter_manager.get_model_parameters()
        conf.sat_solver_config = self.sat_parameters(
            sat_engine=p["sat"]["sat_engine"], road_data=p["sat"]["road_data"]
        )
        return conf

    def parameter_input(self):
        # main method that exposes the parameter input interface to users in a notebook
        data_map = self.data_map() if self.show_map else HTML()
        selection_map = self.selection_map() if self.selection_map else HTML()
        # Create a grid with two columns, splitting space equally
        layout = Layout(grid_template_columns="1fr 1fr")
        return VBox(
            [
                giga_sections.section(
                    title="Country Selection",
                    contents=VBox(
                        [self.data_parameters_input(), HTML("<br/>"), data_map]
                    ),
                    extra_class="dark",
                ).add_class("center"),
                giga_sections.section(
                    'School Selection <span style="color: #787; font-weight: normal">(click to expand)</span>',
                    selection_map,
                    "dark",
                )
                .add_class("center")
                .add_class("expander")
                .add_class("footer"),
                giga_sections.section(
                    "Scenario Selection", self.scenario_parameter_input()
                ),
                giga_sections.section(
                    title="Model Configuration",
                    contents=VBox(
                        [
                            GridBox(
                                [
                                    giga_sections.section(
                                        "Fiber Model",
                                        self.fiber_parameter_manager.input_parameters(),
                                    ),
                                    giga_sections.section(
                                        "Satellite - LEO Model",
                                        self.satellite_parameters_input(),
                                    ),
                                ],
                                layout=layout,
                            ),
                            GridBox(
                                [
                                    giga_sections.section(
                                        "Cellular Model",
                                        self.cellular_parameters_input(),
                                    ),
                                    giga_sections.section(
                                        "P2P Model", self.p2p_parameters_input()
                                    ),
                                ],
                                layout=layout,
                            ),
                            GridBox(
                                [
                                    giga_sections.section(
                                        "Electricity Parameters",
                                        self.electricity_parameters_input(),
                                    ),
                                    giga_sections.section(
                                        "SAT Parameters",
                                        self.sat_parameters_input(),
                                    ),
                                ],
                                layout=layout,
                            ),
                        ],
                    ),
                    extra_class="center",
                ),
            ]
        )
