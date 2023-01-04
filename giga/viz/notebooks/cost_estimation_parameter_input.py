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
    FiberTechnologyCostConf,
    SatelliteTechnologyCostConf,
    CellularTechnologyCostConf,
    MinimumCostScenarioConf,
    SingleTechnologyScenarioConf,
    ElectricityCostConf,
)
from giga.schemas.conf.data import DataSpaceConf
from giga.app.config import ConfigClient, get_config


SCENARIO_PARAMETERS = [
    {
        "parameter_name": "scenario_tpye",
        "parameter_input_name": "Cost Scenario",
        "parameter_interactive": Dropdown(
            options=["Minimum Cost", "Fiber", "Satellite", "Cellular"],
            value="Minimum Cost",
            description="Cost Scenario:",
            style={"description_width": "initial"},
            layout=Layout(width="400px"),
        ),
    },
]

SCENARIO_SHEET_PARAMETERS = [
    {
        "parameter_name": "years_opex",
        "parameter_input_name": "OpEx Years",
        "parameter_interactive": IntSlider(5, min=0, max=10, step=1),
    },
    {
        "parameter_name": "bandwidth_demand",
        "parameter_input_name": "Bandwidth Demand (Mbps)",
        "parameter_interactive": FloatSlider(40, min=1, max=500, step=1),
    },
]

FIBER_MODEL_PARAMETERS = [
    {
        "parameter_name": "per_mbps_cost",
        "parameter_input_name": "Annual cost per Mbps (USD)",
        "parameter_interactive": IntSlider(10, min=0, max=100, step=1),
    },
    {
        "parameter_name": "cost_per_km",
        "parameter_input_name": "Cost Per km (USD)",
        "parameter_interactive": IntSlider(8_900, min=0, max=50_000, step=100),
    },
    {
        "parameter_name": "fixed_costs",
        "parameter_input_name": "Maintenance Cost per km (USD)",
        "parameter_interactive": IntSlider(100, min=0, max=1_000, step=10),
    },
    {
        "parameter_name": "maximum_connection_length",
        "parameter_input_name": "Maximum Connection Length (km)",
        "parameter_interactive": IntSlider(20, min=0, max=100),
    },
    {
        "parameter_name": "power_requirement",
        "parameter_input_name": "Annual Power Required (kWh)",
        "parameter_interactive": IntSlider(500, min=0, max=1_000, step=10),
    },
    {
        "parameter_name": "economies_of_scale",
        "parameter_input_name": "Economies of Scale",
        "parameter_interactive": Checkbox(value=True, description="ON"),
    },
]

SATELLITE_MODEL_PARAMETERS = [
    {
        "parameter_name": "install_costs",
        "parameter_input_name": "Installation Cost (USD)",
        "parameter_interactive": IntSlider(600, min=0, max=4_000, step=10),
    },
    {
        "parameter_name": "per_mbps_cost",
        "parameter_input_name": "Annual cost per Mbps (USD)",
        "parameter_interactive": IntSlider(15, min=0, max=100, step=1),
    },
    {
        "parameter_name": "fixed_costs",
        "parameter_input_name": "Annual Maintenance Cost (USD)",
        "parameter_interactive": IntSlider(0, min=0, max=1_000, step=10),
    },
    {
        "parameter_name": "power_requirement",
        "parameter_input_name": "Annual Power Required (kWh)",
        "parameter_interactive": IntSlider(200, min=0, max=1_000, step=10),
    },
]

CELLULAR_MODEL_PARAMETERS = [
    {
        "parameter_name": "install_costs",
        "parameter_input_name": "Installation Cost (USD)",
        "parameter_interactive": IntSlider(500, min=0, max=2_500, step=10),
    },
    {
        "parameter_name": "per_mbps_cost",
        "parameter_input_name": "Annual cost per Mbps (USD)",
        "parameter_interactive": IntSlider(10, min=0, max=100, step=1),
    },
    {
        "parameter_name": "fixed_costs",
        "parameter_input_name": "Annual Maintenance Cost (USD)",
        "parameter_interactive": IntSlider(0, min=0, max=1_000, step=10),
    },
    {
        "parameter_name": "power_requirement",
        "parameter_input_name": "Annual Power Required (kWh)",
        "parameter_interactive": IntSlider(10, min=0, max=100, step=10),
    },
    {
        "parameter_name": "maximum_range",
        "parameter_input_name": "Maximum Cell Tower Range (km)",
        "parameter_interactive": IntSlider(8, min=0, max=25),
    },
]

ELECTRICITY_MODEL_PARAMETERS = [
    {
        "parameter_name": "per_kwh_cost",
        "parameter_input_name": "Cost per kWh (USD)",
        "parameter_interactive": FloatSlider(0.10, min=0, max=1, step=0.1),
    },
    {
        "parameter_name": "solar_panel_costs",
        "parameter_input_name": "Solar Panel Install Cost (USD)",
        "parameter_interactive": IntSlider(10_000, min=0, max=30_000, step=100),
    }
]

BASELINE_DATA_SPACE_PARAMETERS = [
    {
        "parameter_name": "country_name",
        "parameter_input_name": "Country",
        "parameter_interactive": Dropdown(
            options=["Sample", "Brazil", "Rwanda"],
            value="Sample",
            disabled=True,
            description="Country:",
            layout=Layout(width="400px"),
        ),
    }
]

UPLOADED_DATA_SPACE_PARAMETERS = BASELINE_DATA_SPACE_PARAMETERS + [
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
    xCreates an interactive dashboard in jupyter notebooks that allows users
    to configure data, model, and scenario parameters for connectivity cost estimation
    """

    def __init__(self, local_data_workspace="workspace"):
        self._hashed_sheets = {}
        self.workspace = local_data_workspace

    def fiber_parameters_input(self, sheet_name="fiber"):
        s = sheet(
            sheet_name,
            columns=2,
            rows=len(FIBER_MODEL_PARAMETERS),
            column_headers=False,
            row_headers=False,
            column_width=2,
        )
        name_column = column(
            0, list(map(lambda x: x["parameter_input_name"], FIBER_MODEL_PARAMETERS))
        )
        input_column = column(
            1, list(map(lambda x: x["parameter_interactive"], FIBER_MODEL_PARAMETERS))
        )
        return s

    def satellite_parameters_input(self, sheet_name="satellite"):
        s = sheet(
            sheet_name,
            columns=2,
            rows=len(SATELLITE_MODEL_PARAMETERS),
            column_headers=False,
            row_headers=False,
            column_width=2,
        )
        name_column = column(
            0,
            list(map(lambda x: x["parameter_input_name"], SATELLITE_MODEL_PARAMETERS)),
        )
        input_column = column(
            1,
            list(map(lambda x: x["parameter_interactive"], SATELLITE_MODEL_PARAMETERS)),
        )
        return s

    def cellular_parameters_input(self, sheet_name="cellular"):
        s = sheet(
            sheet_name,
            columns=2,
            rows=len(CELLULAR_MODEL_PARAMETERS),
            column_headers=False,
            row_headers=False,
            column_width=2,
        )
        name_column = column(
            0,
            list(map(lambda x: x["parameter_input_name"], CELLULAR_MODEL_PARAMETERS)),
        )
        input_column = column(
            1,
            list(map(lambda x: x["parameter_interactive"], CELLULAR_MODEL_PARAMETERS)),
        )
        return s

    def electricity_parameters_input(self, sheet_name="electricity"):
        s = sheet(
            sheet_name,
            columns=2,
            rows=len(ELECTRICITY_MODEL_PARAMETERS),
            column_headers=False,
            row_headers=False,
            column_width=2,
        )
        name_column = column(
            0,
            list(map(lambda x: x["parameter_input_name"], ELECTRICITY_MODEL_PARAMETERS)),
        )
        input_column = column(
            1,
            list(map(lambda x: x["parameter_interactive"], ELECTRICITY_MODEL_PARAMETERS)),
        )
        return s

    def fiber_parameters(self, sheet_name="fiber"):
        s = sheet(sheet_name)
        df = to_dataframe(s)
        annual_cost_per_mbps = float(df[df["A"] == "Annual cost per Mbps (USD)"]["B"])
        cost_per_km = float(df[df["A"] == "Cost Per km (USD)"]["B"])
        economies_of_scale = bool(float(df[df["A"] == "Economies of Scale"]["B"]))
        opex_per_km = float(df[df["A"] == "Maintenance Cost per km (USD)"]["B"])
        required_power = float(df[df["A"] == "Annual Power Required (kWh)"]["B"])
        maximum_connection_length = (
            float(df[df["A"] == "Maximum Connection Length (km)"]["B"]) * 1000.0
        )  # meters
        return FiberTechnologyCostConf(
            capex={
                "cost_per_km": cost_per_km,
                "economies_of_scale": economies_of_scale,
            },
            opex={
                "cost_per_km": opex_per_km,
                "annual_bandwidth_cost_per_mbps": annual_cost_per_mbps,
            },
            constraints={
                "maximum_connection_length": maximum_connection_length,
                "required_power": required_power,
                "maximum_bandwithd": 2_000.0,
            },  # should be pulled from defaults
        )

    def satellite_parameters(self, sheet_name="satellite"):
        s = sheet(sheet_name)
        df = to_dataframe(s)
        annual_cost_per_mbps = float(df[df["A"] == "Annual cost per Mbps (USD)"]["B"])
        install_cost = float(df[df["A"] == "Installation Cost (USD)"]["B"])
        maintenance_cost = float(df[df["A"] == "Annual Maintenance Cost (USD)"]["B"])
        required_power = float(df[df["A"] == "Annual Power Required (kWh)"]["B"])
        return SatelliteTechnologyCostConf(
            capex={"fixed_costs": install_cost},
            opex={
                "fixed_costs": maintenance_cost,
                "annual_bandwidth_cost_per_mbps": annual_cost_per_mbps,
            },
            constraints={"maximum_bandwithd": 150.0,  # should be pulled from defaults
                         "required_power": required_power},
        )

    def cellular_parameters(self, sheet_name="cellular"):
        s = sheet(sheet_name)
        df = to_dataframe(s)
        annual_cost_per_mbps = float(df[df["A"] == "Annual cost per Mbps (USD)"]["B"])
        install_cost = float(df[df["A"] == "Installation Cost (USD)"]["B"])
        maintenance_cost = float(df[df["A"] == "Annual Maintenance Cost (USD)"]["B"])
        required_power = float(df[df["A"] == "Annual Power Required (kWh)"]["B"])
        max_range = float(df[df["A"] == "Maximum Cell Tower Range (km)"]["B"]) * 1000.0
        return CellularTechnologyCostConf(
            capex={"fixed_costs": install_cost},
            opex={
                "fixed_costs": maintenance_cost,
                "annual_bandwidth_cost_per_mbps": annual_cost_per_mbps,
            },
            constraints={"maximum_bandwithd": 100.0,  # should be pulled from defaults
                         "required_power": required_power,
                         "maximum_range": max_range},
        )

    def electricity_parameters(self, sheet_name="electricity"):
        s = sheet(sheet_name)
        df = to_dataframe(s)
        cost_per_kwh = float(df[df["A"] == "Cost per kWh (USD)"]["B"])
        install_solar_panels = float(df[df["A"] == "Solar Panel Install Cost (USD)"]["B"])
        return ElectricityCostConf(
            capex={"solar_panel_costs": install_solar_panels,
                   "battery_costs": 0.0}, # TODO: ignore for now
            opex={"cost_per_kwh": cost_per_kwh}
        )

    def _process_nonsheet_scenario_parameters(self, s):
        return {
            "scenario_type": s["scenario_tpye"].value,
            "opex_responsible": "Consumer"#s["opex_responsible"].value,
        }

    def _process_sheet_scenario_parameters(self, s):
        df = to_dataframe(s)
        years_opex = float(df[df["A"] == "OpEx Years"]["B"])
        bandwidth_demand = float(df[df["A"] == "Bandwidth Demand (Mbps)"]["B"])
        return {"years_opex": years_opex, "bandwidth_demand": bandwidth_demand}

    def scenario_parameters(self, sheet_name="scenario"):
        s = self._hashed_sheets[sheet_name]
        nonsheet = self._process_nonsheet_scenario_parameters(s)
        s = sheet(sheet_name)
        from_sheet = self._process_sheet_scenario_parameters(s)
        p = {**nonsheet, **from_sheet}
        if p["scenario_type"] == "Fiber":
            tech_params = self.fiber_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            return SingleTechnologyScenarioConf(
                technology=p["scenario_type"], tech_config=tech_params, **p
            )
        elif p["scenario_type"] == "Satellite":
            tech_params = self.satellite_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            return SingleTechnologyScenarioConf(
                technology=p["scenario_type"], tech_config=tech_params, **p
            )
        elif p["scenario_type"] == "Cellular":
            tech_params = self.cellular_parameters()
            tech_params.electricity_config = self.electricity_parameters()
            p = SingleTechnologyScenarioConf(
                technology=p["scenario_type"], tech_config=tech_params, **p
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

    def data_parameters_input(self, sheet_name="data"):
        self._hashed_sheets[sheet_name] = {
            p["parameter_name"]: p["parameter_interactive"]
            for p in BASELINE_DATA_SPACE_PARAMETERS
        }
        return VBox(
            list(
                map(
                    lambda x: x["parameter_interactive"], BASELINE_DATA_SPACE_PARAMETERS
                )
            )
        )

    def _base_scenario_parameter_input(self, sheet_name="scenario"):
        self._hashed_sheets[sheet_name] = {
            p["parameter_name"]: p["parameter_interactive"] for p in SCENARIO_PARAMETERS
        }
        return VBox(
            list(map(lambda x: x["parameter_interactive"], SCENARIO_PARAMETERS))
        )

    def _sheet_scenario_parameter_input(self, sheet_name="scenario"):
        s = sheet(
            sheet_name,
            columns=2,
            rows=len(SCENARIO_SHEET_PARAMETERS),
            column_headers=False,
            row_headers=False,
            column_width=2,
        )
        name_column = column(
            0, list(map(lambda x: x["parameter_input_name"], SCENARIO_SHEET_PARAMETERS))
        )
        input_column = column(
            1,
            list(map(lambda x: x["parameter_interactive"], SCENARIO_SHEET_PARAMETERS)),
        )
        return s

    def scenario_parameter_input(self, sheet_name="scenario"):
        non_sheet = self._base_scenario_parameter_input(sheet_name=sheet_name)
        sheet = self._sheet_scenario_parameter_input(sheet_name=sheet_name)
        return VBox([non_sheet, sheet])

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

    def _process_baseline_data_parameters(self, s):
        country_id = s["country_name"].value
        config_request = self._updated_param_request(country_id)
        config = ConfigClient(get_config(config_request))
        return DataSpaceConf(
            school_data_conf={
                "country_id": country_id,
                "data": {"file_path": config.school_file, "table_type": "school"},
            },
            fiber_map_conf={
                "map_type": "fiber-nodes",
                "data": {
                    "file_path": config.fiber_file,
                    "table_type": "coordinate-map",
                },
            },
            cell_tower_map_conf={
                "map_type": "cell-towers",
                "data": {
                    "file_path": config.cellular_file,
                    "table_type": "cell-towers",
                },
            },
        )

    def data_parameters(self, sheet_name="data"):
        if sheet_name + UPLOAD_SUFFIX in self._hashed_sheets:
            s = self._hashed_sheets[sheet_name + UPLOAD_SUFFIX]
            return self._process_uploaded_data_parameters(s)
        else:
            s = self._hashed_sheets[sheet_name]
            return self._process_baseline_data_parameters(s)

    def parameter_input(self):
        t1 = HTML(value="<hr><b>Scenario Configuration</b>")
        d = self.data_parameters_input()
        s = self.scenario_parameter_input()
        t2 = HTML(value="<hr><b>Fiber Model Configuration</b>")
        f = self.fiber_parameters_input()
        t3 = HTML(value="<hr><b>Satellite - LEO Model Configuration</b>")
        sa = self.satellite_parameters_input()
        t4 = HTML(value="<hr><b>Cellular Model Configuration</b>")
        sc = self.cellular_parameters_input()
        t5 = HTML(value="<hr><b>Electricity Model Configuration</b>")
        e = self.electricity_parameters_input()
        return VBox([t1, d, s, t2, f, t3, sa, t4, sc, t5, e])
