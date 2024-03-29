import json
from ipywidgets import (
    FileUpload,
    GridBox,
    VBox,
    Layout,
    HTML,
    Output,
)
from IPython.display import display

from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet
from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.conf.country import GigaDefaults

from giga.schemas.conf.models import (
    MinimumCostScenarioConf,
    PriorityScenarioConf,
)
from giga.schemas.conf.data import DataSpaceConf
from giga.app.config_client import ConfigClient
from giga.app.config import get_country_default, get_country_center_zoom

from giga.viz.notebooks.parameters.groups.data_parameter_manager import (
    DataParameterManager,
    country_name_to_key,
)
from giga.viz.notebooks.parameters.groups.scenario_parameter_manager import (
    ScenarioParameterManager,
)
from giga.viz.notebooks.parameters.groups.fiber_technology_parameter_manager import (
    FiberTechnologyParameterManager,
)
from giga.viz.notebooks.parameters.groups.satellite_technology_parameter_manager import (
    SatelliteTechnologyParameterManager,
)
from giga.viz.notebooks.parameters.groups.cellular_technology_parameter_manager import (
    CellularTechnologyParameterManager,
)
from giga.viz.notebooks.parameters.groups.p2p_technology_parameter_manager import (
    P2PTechnologyParameterManager,
)
from giga.viz.notebooks.parameters.groups.electricity_parameter_manager import (
    ElectricityParameterManager,
)
import giga.viz.notebooks.components.html.sections as giga_sections

# TODO: these are for maps, separate them out into unique UI component
from giga.viz.notebooks.data_maps.map_data_layers import MapDataLayers, MapLayersConfig
from giga.viz.notebooks.data_maps.static_data_map import StaticDataMap, DataMapConfig
from giga.viz.notebooks.data_maps.selection_map_data_layers import (
    SelectionMapDataLayers,
    SelectionMapLayersConfig,
)
from traitlets import directional_link


# NOTE: Interface is a work in progress - this will be updated as UX use cases solidify

DASHBOARD_PARAMETERS = [
    {
        "parameter_name": "verbose",
        "parameter_input_name": "Verbose",
        "parameter_interactive": {
            "parameter_type": "bool_checkbox",
            "value": True,
            "description": "",
        },
    }
]

UPLOADED_DATA_SPACE_PARAMETERS = [
    {
        "parameter_name": "fiber_map_upload",
        "parameter_input_name": "Fiber Map",
        "parameter_interactive": FileUpload(
            accept=".csv",
            multiple=False,
            description="Upload Fiber Map",
            layout=Layout(width="400px"),
        ),
    },
    {
        "parameter_name": "cell_tower_map_upload",
        "parameter_input_name": "Cell Tower Map",
        "parameter_interactive": FileUpload(
            accept=".csv",
            multiple=False,
            description="Upload Cell Tower Map",
            layout=Layout(width="400px"),
        ),
    },
]

UPLOAD_SUFFIX = "_upload"
SHOW_MAP = False  # temporary flag to show/hide map
SCHOOL_SELECTION = False
LARGE_COUNTRIES = ['BRA'] # List of countries with large data that needs removal of cell tower layer to improve map loading speed

def constraint_freeze_transform(value):
    if value:
        return False
    return True

def constraint_freeze_transform_fiber(selected_values):
    return 'Fiber' not in selected_values

def constraint_freeze_transform_cellular(selected_values):
    return 'Cellular' not in selected_values

def constraint_freeze_transform_p2p(selected_values):
    return 'P2P' not in selected_values

def constraint_freeze_transform_satellite(selected_values):
    return 'Satellite' not in selected_values


class CostEstimationParameterInput:
    """
    Creates an interactive dashboard in jupyter notebooks that allows users
    to configure data, model, and scenario parameters for connectivity cost estimation
    """

    def __init__(
        self,
        local_data_workspace="workspace",
        data_parameter_manager=None,
        scenario_parameter_manager=None,
        fiber_parameter_manager=None,
        satellite_parameter_manager=None,
        cellular_parameter_manager=None,
        p2p_parameter_manager=None,
        electricity_parameter_manager=None,
        show_map=SHOW_MAP,
        school_selection=SCHOOL_SELECTION,
        show_defaults=True
    ):
        self._hashed_sheets = {}
        self._hashed_data_layers = {}
        self.show_map = show_map
        self.show_defaults = show_defaults
        self.school_selection = school_selection
        self.map_output = Output(
            layout=Layout(display="flex", justify_content="center")
        )
        self.selection_map_output = Output(
            layout=Layout(display="flex", justify_content="center")
        )
        self.workspace = local_data_workspace
        
        self.country_configs = {}
        self.defaults = {}


        self.data_parameter_manager: DataParameterManager = (
            DataParameterManager(workspace=local_data_workspace)
            if data_parameter_manager is None
            else data_parameter_manager
        )
        self.scenario_parameter_manager: ScenarioParameterManager = (
            ScenarioParameterManager()
            if scenario_parameter_manager is None
            else scenario_parameter_manager
        )
        self.fiber_parameter_manager: FiberTechnologyParameterManager = (
            FiberTechnologyParameterManager()
            if fiber_parameter_manager is None
            else fiber_parameter_manager
        )
        self.satellite_parameter_manager: SatelliteTechnologyParameterManager = (
            SatelliteTechnologyParameterManager()
            if satellite_parameter_manager is None
            else satellite_parameter_manager
        )
        self.cellular_parameter_manager: CellularTechnologyParameterManager = (
            CellularTechnologyParameterManager()
            if cellular_parameter_manager is None
            else cellular_parameter_manager
        )
        self.p2p_parameter_manager: P2PTechnologyParameterManager = (
            P2PTechnologyParameterManager()
            if p2p_parameter_manager is None
            else p2p_parameter_manager
        )
        self.electricity_parameter_manager: ElectricityParameterManager = (
            ElectricityParameterManager()
            if electricity_parameter_manager is None
            else electricity_parameter_manager
        )
        self.dashboard_parameter_manager: ParameterSheet = ParameterSheet(
            "dashboard", DASHBOARD_PARAMETERS
        )
        self.managers = {
            "data": [self.data_parameter_manager],
            "scenario": [self.scenario_parameter_manager],
            "technology": [
                self.fiber_parameter_manager,
                self.satellite_parameter_manager,
                self.cellular_parameter_manager,
                self.p2p_parameter_manager,
                self.electricity_parameter_manager,
            ],
        }
        #link techs to their parameters
        techs_selected = self.scenario_parameter_manager.sheet.get_interactive_parameter('technologies')
        for p in self.fiber_parameter_manager.sheet.interactive_parameters:
            directional_link(
                (techs_selected, "value"),
                (p.parameter,"disabled"),
                constraint_freeze_transform_fiber,
            )
        for p in self.cellular_parameter_manager.sheet.interactive_parameters:
            directional_link(
                (techs_selected, "value"),
                (p.parameter,"disabled"),
                constraint_freeze_transform_cellular,
            )
        for p in self.p2p_parameter_manager.sheet.interactive_parameters:
            directional_link(
                (techs_selected, "value"),
                (p.parameter,"disabled"),
                constraint_freeze_transform_p2p,
            )
        for p in self.satellite_parameter_manager.sheet.interactive_parameters:
            directional_link(
                (techs_selected, "value"),
                (p.parameter,"disabled"),
                constraint_freeze_transform_satellite,
            )
        ########

        # link country selection to default parameters for that country
        def update_country_defaults(change):
            country = country_name_to_key(change["new"])
            if country not in self.country_configs:
                self.country_configs[country] = ConfigClient.from_country_defaults(
                    get_country_default(country, workspace=local_data_workspace)
                )
                self.defaults[country] = self.country_configs[country].defaults
            self.set_defaults_for_country(self.defaults[country].model_defaults)

        # update defaults on load
        update_country_defaults(
            {"new": self.data_parameter_manager.interactive_country_parameter.value}
        )
        self.data_parameter_manager.interactive_country_parameter.observe(
            update_country_defaults, names="value"
        )

        # link country selection to map output
        def update_map(change):
            self.map_output.clear_output()
            self.selection_map_output.clear_output()
            country = country_name_to_key(change["new"])

            if country not in self._hashed_data_layers:
                self._hashed_data_layers[country] = self._make_map_layer(country)
            map_layers, _ = self._hashed_data_layers[country]
            
            config_map = DataMapConfig()
            data_map = StaticDataMap(config_map)
            data_map.add_layers((map_layers.layers_no_cell if country in LARGE_COUNTRIES else map_layers.layers))
            m = data_map.get_map(self.defaults[country].data.country_center_tuple, self.defaults[country].data.country_zoom)
            self.data_map_m = m
            with self.map_output:
                data_map.make_static_map_figure(m)
            return self.map_output

        def update_selection_map(change):
            self.selection_map_output.clear_output()
            country = country_name_to_key(change["new"])
            
            if country not in self._hashed_data_layers:
                self._hashed_data_layers[country] = self._make_map_layer(country)
            _, selection_layers = self._hashed_data_layers[country]
            
            config_map = DataMapConfig(no_cell=(True if country in LARGE_COUNTRIES else False))
            data_map = StaticDataMap(config_map)
            m = data_map.get_selection_map(
                self.defaults[country].data.country_center_tuple, self.defaults[country].data.country_zoom, selection_layers
            )
            with self.selection_map_output:
                display(
                    VBox(
                        [
                            HTML(
                                value="To add multiple selections, hold <b>Shift</b> when making a new selection. Double-click a selection to clear it."
                            ),
                            m,
                        ]
                    )
                )

        self.data_parameter_manager.interactive_country_parameter.observe(
            update_map, names="value"
        )
        self.data_parameter_manager.interactive_country_parameter.observe(
            update_selection_map, names="value"
        )

    def set_defaults_for_country(self, new_defaults: GigaDefaults):
        defaults = new_defaults
        self.scenario_parameter_manager.update_country_parameters(
            defaults.scenario.dict()
        )
        self.scenario_parameter_manager.update_techs_parameters(
            defaults.available_tech.dict()
        )
        self.fiber_parameter_manager.update_parameters(defaults.fiber.dict())
        self.satellite_parameter_manager.update_parameters(
            defaults.satellite.dict()
        )
        self.cellular_parameter_manager.update_parameters(defaults.cellular.dict())
        self.electricity_parameter_manager.update_parameters(
            defaults.electricity.dict()
        )
        self.p2p_parameter_manager.update_parameters(defaults.p2p.dict())
        
    @property
    def config(self):
        return {
            "data_parameters": self.data_parameters().dict(),
            "scenario_parameters": self.scenario_parameters().dict(),
        }

    @property
    def config_json(self):
        return json.dumps(self.config)

    def update(self, config):
        if len(config) == 0:
            return
        sp = config["scenario_parameters"]
        if ("scenario_id" in sp and 
            sp["scenario_id"] != "minimum_cost_actual"
            and sp["scenario_id"] != "minimum_cost_giga"
            and sp["scenario_id"] != "priority_cost"
        ):
            raise ValueError(
                f"Unknown scenario id: {config['scenario_parameters']['scenario_id']}"
            )
        
        self.data_parameter_manager.update_parameters(config["data_parameters"])
        self.scenario_parameter_manager.update_parameters(
            sp
        )

        tech_configs_ordered = [] if "technologies" not in sp else [
            t["technology"] for t in sp["technologies"]
        ]
        select_multiple = self.scenario_parameter_manager.sheet.get_interactive_parameter("technologies")
        self.scenario_parameter_manager.set_ordered_techs(tech_configs_ordered)

        tech_configs = {} if "technologies" not in sp else {
            t["technology"]: t for t in sp["technologies"]
        }

        tech_values = []
        if "Fiber" in tech_configs:
            self.fiber_parameter_manager.update_parameters(
                tech_configs.get("Fiber", {})
            )
            tech_values.append("Fiber")
        if "Cellular" in tech_configs:
            self.cellular_parameter_manager.update_parameters(
                tech_configs.get("Cellular", {})
            )
            tech_values.append("Cellular")
        if "P2P" in tech_configs:
            self.p2p_parameter_manager.update_parameters(tech_configs.get("P2P", {}))
            tech_values.append("P2P")
        if "Satellite" in tech_configs:
            self.satellite_parameter_manager.update_parameters(
                tech_configs.get("Satellite", {})
            )
            tech_values.append("Satellite")

        select_multiple.value = tech_values

        self.electricity_parameter_manager.update_parameters(
            sp["technologies"][0].get(
                "electricity_config", {}
            )
        )


    def data_parameters_input(self, sheet_name="data"):
        return self.data_parameter_manager.input_parameters()
    
    def data_parameters(self, sheet_name="data"):
        #return self.all_country_configs[self.data_parameter_manager.get_country_id()].local_workspace_data_space_config
        return self.country_configs[self.data_parameter_manager.get_country_id()].local_workspace_data_space_config
    
    def scenario_parameter_input(self, sheet_name="scenario"):
        return self.scenario_parameter_manager.input_parameters(self.show_defaults)

    def fiber_parameters(self, sheet_name="fiber"):
        return self.fiber_parameter_manager.get_model_parameters()

    def fiber_parameters_input(self, sheet_name="fiber"):
        return self.fiber_parameter_manager.input_parameters()

    def satellite_parameters_input(self, sheet_name="satellite"):
        return self.satellite_parameter_manager.input_parameters(self.show_defaults)

    def satellite_parameters(self, sheet_name="satellite"):
        return self.satellite_parameter_manager.get_model_parameters()

    def cellular_parameters(self, sheet_name="cellular"):
        return self.cellular_parameter_manager.get_model_parameters()

    def cellular_parameters_input(self, sheet_name="cellular"):
        return self.cellular_parameter_manager.input_parameters(self.show_defaults)

    def p2p_parameters(self, sheet_name="p2p"):
        return self.p2p_parameter_manager.get_model_parameters()

    def p2p_parameters_input(self, sheet_name="p2p"):
        return self.p2p_parameter_manager.input_parameters(self.show_defaults)

    def electricity_parameters_input(self, sheet_name="electricity"):
        return self.electricity_parameter_manager.input_parameters(self.show_defaults)

    def electricity_parameters(self, sheet_name="electricity"):
        return self.electricity_parameter_manager.get_model_parameters()

    def dashboard_parameters_input(self, sheet_name="dashboard"):
        return self.dashboard_parameter_manager.input_parameters()

    def dashboard_parameters(self, sheet_name="dashboard"):
        verbose = self.dashboard_parameter_manager.get_parameter_value("verbose")
        return {"verbose": verbose}

    def freeze(self):
        for manager_collection in self.managers.values():
            for m in manager_collection:
                m.freeze()

    def unfreeze(self):
        for manager_collection in self.managers.values():
            for m in manager_collection:
                m.unfreeze()

        select_multiple = self.scenario_parameter_manager.sheet.get_interactive_parameter("technologies")
        # some things need to remain frozen
        p_fiber = "Fiber" in select_multiple.value
        if not p_fiber:
            for p in self.fiber_parameter_manager.sheet.interactive_parameters:
                p.parameter.disabled = True
        p_cell = "Cellular" in select_multiple.value
        if not p_cell:
            for p in self.cellular_parameter_manager.sheet.interactive_parameters:
                p.parameter.disabled = True
        p_p2p = "P2P" in select_multiple.value
        if not p_p2p:
            for p in self.p2p_parameter_manager.sheet.interactive_parameters:
                p.parameter.disabled = True
        p_sat = "Satellite" in select_multiple.value
        if not p_sat:
            for p in self.satellite_parameter_manager.sheet.interactive_parameters:
                p.parameter.disabled = True
    
    def all_tech_config(self):
        p = self.scenario_parameter_manager.get_model_parameters()
        if p["scenario_type"] == "Lowest Cost":
            conf = MinimumCostScenarioConf(**p)
        else: # priorities scenario
            conf = PriorityScenarioConf(**p)
        techs = []
        
        fiber_params = self.fiber_parameters()
        fiber_params.electricity_config = self.electricity_parameters()
        techs.append(fiber_params)
        
        cellular_params = self.cellular_parameters()
        cellular_params.electricity_config = self.electricity_parameters()
        techs.append(cellular_params)

        p2p_params = self.p2p_parameters()
        p2p_params.electricity_config = self.electricity_parameters()
        techs.append(p2p_params)

        satellite_params = self.satellite_parameters()
        satellite_params.electricity_config = self.electricity_parameters()
        techs.append(satellite_params)
        
        conf.technologies = techs
        conf.required_power_per_school = self.electricity_parameter_manager.sheet.get_parameter_value("required_power_per_school")
        if p["use_budget_constraint"]:
            conf.cost_minimizer_config.budget_constraint = p["cost_minimizer_config"][
                "budget_constraint"
            ]
        return conf

    def scenario_parameters(self, sheet_name="scenario"):
        p = self.scenario_parameter_manager.get_model_parameters()
        if p["scenario_type"] == "Lowest Cost - Heuristic A":
            p["scenario_id"] = "minimum_cost_a"
            conf = MinimumCostScenarioConf(**p)
        elif p["scenario_type"] == "Lowest Cost - Heuristic G":
            p["scenario_id"] = "minimum_cost_g"
            conf = MinimumCostScenarioConf(**p)
        else: # priorities scenario
            conf = PriorityScenarioConf(**p)
        techs_selected = self.scenario_parameter_manager.get_ordered_techs()
        techs = []
        for i in range(len(techs_selected)):
            if techs_selected[i]=='Fiber':
                fiber_params = self.fiber_parameters()
                fiber_params.electricity_config = self.electricity_parameters()
                techs.append(fiber_params)
            elif techs_selected[i]=='Cellular':
                cellular_params = self.cellular_parameters()
                cellular_params.electricity_config = self.electricity_parameters()
                techs.append(cellular_params)
            elif techs_selected[i]=='P2P':
                p2p_params = self.p2p_parameters()
                p2p_params.electricity_config = self.electricity_parameters()
                techs.append(p2p_params)
            elif techs_selected[i]=='Satellite':
                satellite_params = self.satellite_parameters()
                satellite_params.electricity_config = self.electricity_parameters()
                techs.append(satellite_params)
        
        conf.technologies = techs
        conf.required_power_per_school = self.electricity_parameter_manager.sheet.get_parameter_value("required_power_per_school")
        if p["use_budget_constraint"]:
            conf.cost_minimizer_config.budget_constraint = p["cost_minimizer_config"][
                "budget_constraint"
            ]
        return conf

    def get_selected_schools(self):
        country = self.data_parameters().school_data_conf.country_id
        _, selection_layer = self._hashed_data_layers[country]
        return selection_layer.selected_schools

    def set_selected_schools(self, schools):
        country = self.data_parameters().school_data_conf.country_id
        if country not in self._hashed_data_layers:
            layer, selection_layer = self._make_map_layer(country)
        else:
            layer, selection_layer = self._hashed_data_layers[country]
        selection_layer.set_selected_schools(schools)
        self._hashed_data_layers[country] = layer, selection_layer


    def data_parameters_upload_input(self, sheet_name="data"):
        self._hashed_sheets[sheet_name + UPLOAD_SUFFIX] = {
            p["parameter_name"]: p["parameter_interactive"]
            for p in UPLOADED_DATA_SPACE_PARAMETERS
        }
        return VBox(
            list(
                map(
                    lambda x: x["parameter_interactive"], UPLOADED_DATA_SPACE_PARAMETERS
                )
            )
        )

    def _make_map_layer(self, country):
        country_key = country #country_name_to_key(country)
        config_client = ConfigClient(self.defaults[country_key])
        data_space = ModelDataSpace(config_client.local_workspace_data_space_config)
        config_layers = MapLayersConfig()
        layer = MapDataLayers(data_space, config_layers)
        selection_layer = SelectionMapDataLayers.from_loaded_data_layers(
            SelectionMapLayersConfig(), layer
        )
        return layer, selection_layer
    
    def _make_selected_map_layer(self, country):
        country_key = country
        config_client = ConfigClient(self.defaults[country_key])
        data_space = ModelDataSpace(config_client.local_workspace_data_space_config)
        data_space_selected = data_space.filter_schools(self.get_selected_schools())
        config_layers = MapLayersConfig()
        layer = MapDataLayers(data_space_selected, config_layers)
        center_selected, zoom_selected = get_country_center_zoom(data_space_selected.schools_to_frame(), max_zoom_level=12)
        return layer, center_selected, zoom_selected

    def data_map(self):
        # TODO (max): this is a placeholder for a static map in the notebook that will be refactored out once the UI implementation is complete
        self.map_output.clear_output()
        country = self.data_parameters().school_data_conf.country_id
        if country not in self._hashed_data_layers:
            self._hashed_data_layers[country] = self._make_map_layer(country)
        map_layers, _ = self._hashed_data_layers[country]
        config_map = DataMapConfig()
        data_map = StaticDataMap(config_map)
        data_map.add_layers((map_layers.layers_no_cell if country in LARGE_COUNTRIES else map_layers.layers))
        m = data_map.get_map(self.defaults[country].data.country_center_tuple, self.defaults[country].data.country_zoom)
        self.data_map_m = m
        with self.map_output:
            data_map.make_static_map_figure(m)
        return self.map_output
    
    def selected_data_map(self):
        country = self.data_parameters().school_data_conf.country_id
        map_layers, center_selected, zoom_selected = self._make_selected_map_layer(country)
        config_map = DataMapConfig()
        data_map = StaticDataMap(config_map)
        data_map.add_layers((map_layers.layers_no_cell if country in LARGE_COUNTRIES else map_layers.layers))
        m = data_map.get_map([center_selected['lat'], center_selected['lon']], zoom_selected)
        self.data_map_m_selected = m
        return m

    def selection_map(self):
        self.selection_map_output.clear_output()
        country = self.data_parameters().school_data_conf.country_id
        if country not in self._hashed_data_layers:
            self._hashed_data_layers[country] = self._make_map_layer(country)
        _, selection_layers = self._hashed_data_layers[country]
        config_map = DataMapConfig(no_cell=(True if country in LARGE_COUNTRIES else False))
        data_map = StaticDataMap(config_map)
        m = data_map.get_selection_map(
            self.defaults[country].data.country_center_tuple, self.defaults[country].data.country_zoom, selection_layers
        )
        with self.selection_map_output:
            display(
                VBox(
                    [
                        HTML(
                            value="To add multiple selections, hold <b>Shift</b> when making a new selection. Double-click a selection to clear it.<br> To upload schools, click the <b>Upload Schools</b> button and select a csv file that contains a <b>school_id</b> column."
                        ),
                        m,
                    ]
                )
            )
        return self.selection_map_output

    def model_parameter_input(self):
        """Exposes sub-model parameters only."""
        # Create a grid with two columns, splitting space equally
        layout = Layout(grid_template_columns="1fr 1fr")
        return VBox(
            [
                GridBox(
                    [
                        giga_sections.section(
                            "Fiber Model",
                            self.fiber_parameter_manager.input_parameters(self.show_defaults),
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
                    ],
                ),
            ],
        )

    def country_default_parameter_input(self):
        """Exposes country default parameters only."""
        return VBox([
            giga_sections.section(
                title="Country Model Defaults",
                contents=self.model_parameter_input(),
                extra_class="center",
            )

        ])

    def parameter_input(self):
        # main method that exposes the parameter input interface to users in a notebook
        data_map = self.data_map() if self.show_map else HTML()
        selection_map = self.selection_map() if self.selection_map else HTML()
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
                    contents=self.model_parameter_input(),
                    extra_class="center",
                ),
                giga_sections.section(
                    title = 'Verbose',
                    contents = self.dashboard_parameters_input(),
                    extra_class = 'center'
                )
            ]
        )
