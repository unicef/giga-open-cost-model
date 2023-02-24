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
)
from ipysheet import sheet, column, to_dataframe

from giga.schemas.conf.models import (
    MinimumCostScenarioConf,
    SingleTechnologyScenarioConf,
    ElectricityCostConf,
)
from giga.schemas.conf.data import DataSpaceConf
from giga.app.config import ConfigClient, get_config

from giga.viz.notebooks.parameters.groups.data_paramter_manager import (
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
from giga.viz.notebooks.parameters.groups.electricity_parameter_manager import (
    ElectricityParameterManager,
)


# NOTE: Interface is a work in progress - this will be updated as UX use cases solidify

DASHBOARD_PARAMETERS = [
    {
        "parameter_name": "verbose",
        "parameter_input_name": "Verbose",
        "parameter_interactive": Checkbox(value=True, description="ON"),
    },
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


class CostEstimationParameterInput:
    """
    Creates an interactive dashboard in jupyter notebooks that allows users
    to configure data, model, and scenario parameters for connectivity cost estimation
    """

    def __init__(
        self,
        local_data_workspace="workspace",
        defaults=None,
        data_parameter_manager=None,
        scenario_parameter_manager=None,
        fiber_parameter_manager=None,
        satellite_parameter_manager=None,
        cellular_parameter_manager=None,
        electricity_parameter_manager=None,
    ):
        self._hashed_sheets = {}
        self.workspace = local_data_workspace
        self.defaults = defaults
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
        self.electricity_parameter_manager = (
            ElectricityParameterManager()
            if electricity_parameter_manager is None
            else electricity_parameter_manager
        )
        self.managers = {
            "data": [self.data_parameter_manager],
            "scenario": [self.scenario_parameter_manager],
            "technology": [
                self.fiber_parameter_manager,
                self.satellite_parameter_manager,
                self.cellular_parameter_manager,
            ],
        }

    @property
    def config(self):
        return {
            "data_parameters": self.data_parameters().dict(),
            "scenario_parameters": self.scenario_parameters().dict(),
        }

    @property
    def config_json(self):
        return json.dumps(self.config)

    @staticmethod
    def from_config_single_tech(config, local_data_workspace="workspace"):
        # This static method creates a input dashboard for the single technology scenario
        tech_config = config["scenario_parameters"]["tech_config"]
        tech = config["scenario_parameters"]["technology"]
        scenario_parameter_manager = ScenarioParameterManager.from_config(
            config["scenario_parameters"]
        )
        electricity_parameter_manager = ElectricityParameterManager.from_config(
            tech_config["electricity_config"]
        )
        data_parameter_manager = DataParameterManager.from_config(
            config["data_parameters"], workspace=local_data_workspace
        )
        if tech == "Satellite":
            satellite_parameter_manager = (
                SatelliteTechnologyParameterManager.from_config(tech_config)
            )
            return CostEstimationParameterInput(
                local_data_workspace=local_data_workspace,
                data_parameter_manager=data_parameter_manager,
                scenario_parameter_manager=scenario_parameter_manager,
                satellite_parameter_manager=satellite_parameter_manager,
                electricity_parameter_manager=electricity_parameter_manager,
            )
        elif tech == "Cellular":
            cellular_parameter_manager = CellularTechnologyParameterManager.from_config(
                tech_config
            )
            return CostEstimationParameterInput(
                local_data_workspace=local_data_workspace,
                data_parameter_manager=data_parameter_manager,
                scenario_parameter_manager=scenario_parameter_manager,
                satellite_parameter_manager=satellite_parameter_manager,
                electricity_parameter_manager=electricity_parameter_manager,
            )
        elif tech == "Fiber":
            fiber_parameter_manager = FiberTechnologyParameterManager.from_config(
                tech_config
            )
            return CostEstimationParameterInput(
                local_data_workspace=local_data_workspace,
                data_parameter_manager=data_parameter_manager,
                scenario_parameter_manager=scenario_parameter_manager,
                fiber_parameter_manager=fiber_parameter_manager,
                electricity_parameter_manager=electricity_parameter_manager,
            )
        else:
            raise ValueError(f"Unknown technology name: {tech}")

    @staticmethod
    def from_config_minimum_cost(config, local_data_workspace="workspace"):
        # This static method creates a input dashboard for the minimum cost scenario
        tech_configs = {
            t["technology"]: t for t in config["scenario_parameters"]["technologies"]
        }
        data_parameter_manager = DataParameterManager.from_config(
            config["data_parameters"], workspace=local_data_workspace
        )
        scenario_parameter_manager = ScenarioParameterManager.from_config(
            config["scenario_parameters"]
        )
        fiber_parameter_manager = FiberTechnologyParameterManager.from_config(
            tech_configs.get("Fiber", {})
        )
        satellite_parameter_manager = SatelliteTechnologyParameterManager.from_config(
            tech_configs.get("Satellite", {})
        )
        cellular_parameter_manager = CellularTechnologyParameterManager.from_config(
            tech_configs.get("Cellular", {})
        )
        electricity_parameter_manager = ElectricityParameterManager.from_config(
            config["scenario_parameters"]["technologies"][0].get(
                "electricity_config", {}
            )
        )
        return CostEstimationParameterInput(
            local_data_workspace=local_data_workspace,
            data_parameter_manager=data_parameter_manager,
            scenario_parameter_manager=scenario_parameter_manager,
            fiber_parameter_manager=fiber_parameter_manager,
            satellite_parameter_manager=satellite_parameter_manager,
            cellular_parameter_manager=cellular_parameter_manager,
            electricity_parameter_manager=electricity_parameter_manager,
        )

    @staticmethod
    def from_config(config, local_data_workspace="workspace"):
        # This static method is used to create a CostEstimationParameterInput object from a config file
        if len(config) == 0:
            return CostEstimationParameterInput(
                local_data_workspace=local_data_workspace
            )
        if config["scenario_parameters"]["scenario_id"] == "single_tech_cost":
            return CostEstimationParameterInput.from_config_single_tech(
                config, local_data_workspace
            )
            # need to pull out by technology to pass in args explicitly
        elif config["scenario_parameters"]["scenario_id"] == "minimum_cost":
            return CostEstimationParameterInput.from_config_minimum_cost(
                config, local_data_workspace
            )
        else:
            raise ValueError(
                f"Unknown scenario id: {config['scenario_parameters']['scenario_id']}"
            )

    def update(self, config):
        if len(config) == 0:
            return
        if config["scenario_parameters"]["scenario_id"] == "minimum_cost":
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
            else:
                raise ValueError(f"Unknown technology name: {tech}")
        else:
            raise ValueError(
                f"Unknown scenario id: {config['scenario_parameters']['scenario_id']}"
            )

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

    def electricity_parameters_input(self, sheet_name="electricity"):
        return self.electricity_parameter_manager.input_parameters()

    def electricity_parameters(self, sheet_name="electricity"):
        return self.electricity_parameter_manager.get_model_parameters()

    def dashboard_parameters_input(self, sheet_name="dashboard"):
        s = sheet(
            sheet_name,
            columns=2,
            rows=len(DASHBOARD_PARAMETERS),
            column_headers=False,
            row_headers=False,
            column_width=2,
        )
        name_column = column(
            0, list(map(lambda x: x["parameter_input_name"], DASHBOARD_PARAMETERS))
        )
        input_column = column(
            1, list(map(lambda x: x["parameter_interactive"], DASHBOARD_PARAMETERS))
        )
        return s

    def dashboard_parameters(self, sheet_name="dashboard"):
        s = sheet(sheet_name)
        df = to_dataframe(s)
        verbose = bool(float(df[df["A"] == "Verbose"]["B"]))
        return {"verbose": verbose}

    def scenario_parameters(self, sheet_name="scenario"):
        p = self.scenario_parameter_manager.get_model_parameters()
        if p["scenario_type"] == "Fiber Only":
            tech_params = self.fiber_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            return SingleTechnologyScenarioConf(
                technology="Fiber", tech_config=tech_params, **p
            )
        elif p["scenario_type"] == "Satellite Only":
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
        else:
            fiber_params = self.fiber_parameters()
            satellite_params = self.satellite_parameters()
            cellular_params = self.cellular_parameters()
            fiber_params.electricity_config = self.electricity_parameters()
            satellite_params.electricity_config = self.electricity_parameters()
            cellular_params.electricity_config = self.electricity_parameters()
            p = MinimumCostScenarioConf(
                **p, technologies=[fiber_params, satellite_params, cellular_params]
            )
            p.technologies[2] = cellular_params
            return p

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

    def _updated_param_request(self, country):
        return [f"data={country.lower()}", f"data.workspace={self.workspace}"]

    def _process_uploaded_data_parameters(self, s):
        country_id = s["country_name"].value
        config_request = self._updated_param_request(country_id)
        config = ConfigClient(get_config(config_request))
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

    def parameter_input(self):
        # main method that exposes the parameter input interface to users in a notebook
        t1 = HTML(value="<hr><b>Scenario Configuration</b>")
        d = self.data_parameters_input()
        s = self.scenario_parameter_input()
        t2 = HTML(value="<hr><b>Fiber Model Configuration</b>")
        f = self.fiber_parameter_manager.input_parameters()
        t3 = HTML(value="<hr><b>Satellite - LEO Model Configuration</b>")
        sa = self.satellite_parameters_input()
        t4 = HTML(value="<hr><b>Cellular Model Configuration</b>")
        sc = self.cellular_parameters_input()
        t5 = HTML(value="<hr><b>Electricity Model Configuration</b>")
        e = self.electricity_parameters_input()
        t6 = HTML(value="<hr><b>Dashboard Configuration</b>")
        da = self.dashboard_parameters_input()
        return VBox([t1, d, s, t2, f, t3, sa, t4, sc, t5, e, t6, da])
