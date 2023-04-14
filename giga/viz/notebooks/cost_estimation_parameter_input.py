import json
from ipywidgets import (
    FloatSlider,
    IntSlider,
    Checkbox,
    Dropdown,
    FileUpload,
    VBox,
    Layout,
    HTML,
    Output,
)
from IPython.display import display

from giga.viz.notebooks.parameters.parameter_sheet import ParameterSheet
from giga.data.space.model_data_space import ModelDataSpace

from giga.schemas.conf.models import (
    MinimumCostScenarioConf,
    SingleTechnologyScenarioConf,
    ElectricityCostConf,
)
from giga.schemas.conf.data import DataSpaceConf
from giga.app.config_client import ConfigClient
from giga.app.config import get_country_defaults

from giga.viz.notebooks.parameters.groups.data_parameter_manager import (
    DataParameterManager,
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

# TODO: these are for maps, separate them out into unique UI component
from giga.viz.notebooks.data_maps.map_data_layers import MapDataLayers, MapLayersConfig
from giga.viz.notebooks.data_maps.static_data_map import StaticDataMap, DataMapConfig


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
    ):
        self._hashed_sheets = {}
        self._hashed_data_layers = {}
        self.show_map = show_map
        self.map_output = Output(
            layout=Layout(display="flex", justify_content="center")
        )
        self.workspace = local_data_workspace
        self.defaults = {
            k: ConfigClient.from_registered_country(k, local_data_workspace).defaults
            for k, v in get_country_defaults(workspace=local_data_workspace).items()
        }
        self.data_parameter_manager = (
            DataParameterManager(workspace=local_data_workspace)
            if data_parameter_manager is None
            else data_parameter_manager
        )
        self.scenario_parameter_manager = (
            ScenarioParameterManager()
            if scenario_parameter_manager is None
            else scenario_parameter_manager
        )
        self.fiber_parameter_manager = (
            FiberTechnologyParameterManager()
            if fiber_parameter_manager is None
            else fiber_parameter_manager
        )
        self.satellite_parameter_manager = (
            SatelliteTechnologyParameterManager()
            if satellite_parameter_manager is None
            else satellite_parameter_manager
        )
        self.cellular_parameter_manager = (
            CellularTechnologyParameterManager()
            if cellular_parameter_manager is None
            else cellular_parameter_manager
        )
        self.p2p_parameter_manager = (
            P2PTechnologyParameterManager()
            if p2p_parameter_manager is None
            else p2p_parameter_manager
        )
        self.electricity_parameter_manager = (
            ElectricityParameterManager()
            if electricity_parameter_manager is None
            else electricity_parameter_manager
        )
        self.dashboard_parameter_manager = ParameterSheet(
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
            ],
        }
        # link country selection to default parameters for that country
        def update_country_defaults(change):
            country = change["new"].lower()
            defaults = self.defaults[country].model_defaults
            self.scenario_parameter_manager.update_country_parameters(
                defaults.scenario.dict()
            )
            self.fiber_parameter_manager.update_parameters(defaults.fiber.dict())
            self.satellite_parameter_manager.update_parameters(
                defaults.satellite.dict()
            )
            self.cellular_parameter_manager.update_parameters(defaults.cellular.dict())
            self.electricity_parameter_manager.update_parameters(
                defaults.electricity.dict()
            )

        self.data_parameter_manager.interactive_country_parameter.observe(
            update_country_defaults, names="value"
        )

        # link country selection to map output
        def update_map(change):
            self.map_output.clear_output()
            country = change["new"].lower()
            config_map = DataMapConfig()
            data_map = StaticDataMap(config_map)
            if country not in self._hashed_data_layers:
                self._hashed_data_layers[country] = self._make_map_layer(country)
            map_layers = self._hashed_data_layers[country]
            if country == "brazil":
                # handle brazil as a one off for now
                config_map = DataMapConfig(zoom=3)
                data_map = StaticDataMap(config_map)
                data_map.add_layers(
                    [map_layers.school_layer, map_layers.fiber_layer]
                )  # ignore cell tower layer for now
                m = data_map.get_map(self.defaults[country].data.country_center_tuple)
            else:
                config_map = DataMapConfig()
                data_map = StaticDataMap(config_map)
                data_map.add_layers(map_layers.layers)
                m = data_map.get_map(self.defaults[country].data.country_center_tuple)
            with self.map_output:
                display(m)

        self.data_parameter_manager.interactive_country_parameter.observe(
            update_map, names="value"
        )

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
        if (
            config["scenario_parameters"]["scenario_id"] == "minimum_cost"
            or config["scenario_parameters"]["scenario_id"] == "budget_constrained"
        ):
            tech_configs = {
                t["technology"]: t
                for t in config["scenario_parameters"]["technologies"]
            }
            self.data_parameter_manager.update_parameters(config["data_parameters"])
            self.scenario_parameter_manager.update_parameters(
                config["scenario_parameters"]
            )
            self.cellular_parameter_manager.update_parameters(
                tech_configs.get("Cellular", {})
            )
            self.satellite_parameter_manager.update_parameters(
                tech_configs.get("Satellite", {})
            )
            self.fiber_parameter_manager.update_parameters(
                tech_configs.get("Fiber", {})
            )
            self.p2p_parameter_manager.update_parameters(tech_configs.get("P2P", {}))
            self.electricity_parameter_manager.update_parameters(
                config["scenario_parameters"]["technologies"][0].get(
                    "electricity_config", {}
                )
            )
            # need to pull out by technology to pass in args explicitly
        elif config["scenario_parameters"]["scenario_id"] == "single_tech_cost":
            tech_config = config["scenario_parameters"]["tech_config"]
            tech = config["scenario_parameters"]["technology"]
            self.data_parameter_manager.update_parameters(config["data_parameters"])
            self.scenario_parameter_manager.update_parameters(
                config["scenario_parameters"]
            )
            self.electricity_parameter_manager.update_parameters(
                tech_config["electricity_config"]
            )
            if tech == "Satellite":
                self.satellite_parameter_manager.update_parameters(tech_config)
            elif tech == "Cellular":
                self.cellular_parameter_manager.update_parameters(tech_config)
            elif tech == "Fiber":
                self.fiber_parameter_manager.update_parameters(tech_config)
            elif tech == "P2P":
                self.p2p_parameter_manager.update_parameters(tech_config)
            else:
                raise ValueError(f"Unknown technology name: {tech}")
        else:
            raise ValueError(
                f"Unknown scenario id: {config['scenario_parameters']['scenario_id']}"
            )

    def get_update_country_cb(self):

        return fn

    def data_parameters_input(self, sheet_name="data"):
        return self.data_parameter_manager.input_parameters()

    def data_parameters(self, sheet_name="data"):
        return self.data_parameter_manager.get_model_parameters()

    def scenario_parameter_input(self, sheet_name="scenario"):
        return self.scenario_parameter_manager.input_parameters()

    def fiber_parameters(self, sheet_name="fiber"):
        return self.fiber_parameter_manager.get_model_parameters()

    def fiber_parameters_input(self, sheet_name="fiber"):
        return self.fiber_parameter_manager.input_parameters()

    def satellite_parameters_input(self, sheet_name="satellite"):
        return self.satellite_parameter_manager.input_parameters()

    def satellite_parameters(self, sheet_name="satellite"):
        return self.satellite_parameter_manager.get_model_parameters()

    def cellular_parameters(self, sheet_name="cellular"):
        return self.cellular_parameter_manager.get_model_parameters()

    def cellular_parameters_input(self, sheet_name="cellular"):
        return self.cellular_parameter_manager.input_parameters()

    def p2p_parameters(self, sheet_name="p2p"):
        return self.p2p_parameter_manager.get_model_parameters()

    def p2p_parameters_input(self, sheet_name="p2p"):
        return self.p2p_parameter_manager.input_parameters()

    def electricity_parameters_input(self, sheet_name="electricity"):
        return self.electricity_parameter_manager.input_parameters()

    def electricity_parameters(self, sheet_name="electricity"):
        return self.electricity_parameter_manager.get_model_parameters()

    def dashboard_parameters_input(self, sheet_name="dashboard"):
        return self.dashboard_parameter_manager.input_parameters()

    def dashboard_parameters(self, sheet_name="dashboard"):
        verbose = self.dashboard_parameter_manager.get_parameter_value("verbose")
        return {"verbose": verbose}

    def scenario_parameters(self, sheet_name="scenario"):
        p = self.scenario_parameter_manager.get_model_parameters()
        if p["scenario_type"] == "Fiber Only":
            tech_params = self.fiber_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            return SingleTechnologyScenarioConf(
                technology="Fiber", tech_config=tech_params, **p
            )
        elif p["scenario_type"] == "Satellite LEO Only":
            tech_params = self.satellite_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            return SingleTechnologyScenarioConf(
                technology="Satellite", tech_config=tech_params, **p
            )
        elif p["scenario_type"] == "Cellular Only":
            tech_params = self.cellular_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            p = SingleTechnologyScenarioConf(
                technology="Cellular", tech_config=tech_params, **p
            )
            p.tech_config = tech_params
            return p
        elif p["scenario_type"] == "P2P Only":
            tech_params = self.p2p_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            p = SingleTechnologyScenarioConf(
                technology="P2P", tech_config=tech_params, **p
            )
            p.tech_config = tech_params
            return p
        else:
            fiber_params = self.fiber_parameters()
            satellite_params = self.satellite_parameters()
            cellular_params = self.cellular_parameters()
            p2p_params = self.p2p_parameters()
            fiber_params.electricity_config = self.electricity_parameters()
            satellite_params.electricity_config = self.electricity_parameters()
            cellular_params.electricity_config = self.electricity_parameters()
            p2p_params.electricity_config = self.electricity_parameters()
            conf = MinimumCostScenarioConf(
                **p,
                technologies=[
                    fiber_params,
                    satellite_params,
                    cellular_params,
                    p2p_params,
                ],
            )
            conf.technologies[2] = cellular_params
            conf.technologies[3] = p2p_params
            if p["scenario_type"] == "Budget Constrained":
                conf.cost_minimizer_config.budget_constraint = p[
                    "cost_minimizer_config"
                ]["budget_constraint"]
                conf.scenario_id = "budget_constrained"
            return conf

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

    def _process_uploaded_data_parameters(self, s):
        country_id = s["country_name"].value
        config = ConfigClient.from_registered_country(
            country_id.lower(), self.workspace
        )
        school_dataset = config.school_file
        content = s["fiber_map_upload"].value[0].content
        return DataSpaceConf(
            school_data_conf={
                "country_id": country_id,
                "data": {"file_path": school_dataset, "table_type": "school"},
            },
            fiber_map_conf={
                "map_type": "fiber-nodes",
                "data": {"uploaded_content": content, "table_type": "coordinate-map"},
            },
        )

    def _make_map_layer(self, country):
        config_client = ConfigClient(self.defaults[country])
        data_space = ModelDataSpace(config_client.local_workspace_data_space_config)
        config_layers = MapLayersConfig()
        return MapDataLayers(data_space, config_layers)

    def data_map(self):
        # TODO (max): this is a placeholder for a static map in the notebook that will be refactored out once the UI implementation is complete
        country = self.data_parameters().school_data_conf.country_id
        if country not in self._hashed_data_layers:
            self._hashed_data_layers[country] = self._make_map_layer(country)
        map_layers = self._hashed_data_layers[country]
        if country == "brazil":
            # handle brazil as a one off for now
            config_map = DataMapConfig(zoom=3)
            data_map = StaticDataMap(config_map)
            data_map.add_layers(
                [map_layers.school_layer, map_layers.fiber_layer]
            )  # ignore cell tower layer for now
            m = data_map.get_map(self.defaults[country].data.country_center_tuple)
        else:
            config_map = DataMapConfig()
            data_map = StaticDataMap(config_map)
            data_map.add_layers(map_layers.layers)
            m = data_map.get_map(self.defaults[country].data.country_center_tuple)
        with self.map_output:
            display(m)
        return self.map_output

    def parameter_input(self):
        # main method that exposes the parameter input interface to users in a notebook
        # TODO (max): remove this once the UI implementation is complete
        data_map = self.data_map() if self.show_map else HTML()
        return VBox(
            [
                HTML(value="<hr><b>Country Selection</b>"),
                self.data_parameters_input(),
                data_map,
                HTML(value="<hr><b>Scenario Selection</b>"),
                self.scenario_parameter_input(),
                HTML(value="<hr><b>Fiber Model Configuration</b>"),
                self.fiber_parameter_manager.input_parameters(),
                HTML(value="<hr><b>Satellite - LEO Model Configuration</b>"),
                self.satellite_parameters_input(),
                HTML(value="<hr><b>Cellular Model Configuration</b>"),
                self.cellular_parameters_input(),
                HTML(value="<hr><b>P2P Model Configuration</b>"),
                self.p2p_parameters_input(),
                HTML(value="<hr><b>Electricity Model Configuration</b>"),
                self.electricity_parameters_input(),
                HTML(value="<hr><b>Dashboard Configuration</b>"),
                self.dashboard_parameters_input(),
                HTML(value="<hr>"),
            ]
        )
