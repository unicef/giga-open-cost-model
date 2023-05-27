from pydantic import BaseModel
import pandas as pd
import numpy as np
import math

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import OutputSpace


class ProjectOverview(BaseModel):

    total_students: int
    total_schools: int
    schools_connected_current: int
    schools_connected_projected: int
    students_connected_current: int
    students_connected_projected: int
    connected_percentage_current: float
    connected_percentage_projected: float
    average_mbps: float


DEFAULT_BINS = [0, 5_000, 10_000, 15_000, 20_000, np.inf]
DEFAULT_NAMES = ["5km", "10km", "15km", "20km", "20km+"]

MILLION = 1_000_000


class ResultStats:
    def __init__(self, data_space: ModelDataSpace, output_space: OutputSpace, config):
        self.output_space = output_space
        self.data_space = data_space
        self.config = config
        self.complete_school_table = data_space.all_schools.to_data_frame()
        # computed properties are cached
        self._output_cost_table = None
        self._output_cost_table_full = None
        self._new_connected_schools = None
        self._project_overview = None

    @property
    def num_project_schools(self):
        return len(self.output_cost_table)

    @property
    def output_cost_table_full(self):
        if self._output_cost_table_full is None:
            self._output_cost_table_full = self.data_space.school_outputs_to_frame(
                self.output_space.full_results_table(self.config.years_opex)
            )
            self._output_cost_table_full["total_cost_per_student"] = (
                self._output_cost_table_full["total_cost"]
                / self._output_cost_table_full["num_students"]
            )
        return self._output_cost_table_full

    @property
    def output_cost_table(self):
        if self._output_cost_table is None:
            full_table = self.output_cost_table_full
            self._output_cost_table = full_table[full_table["total_cost"] != math.inf]
        return self._output_cost_table

    @property
    def new_connected_schools(self):
        if self._new_connected_schools is None:
            self._new_connected_schools = self.output_cost_table[
                self.output_cost_table["feasible"] == True
            ]
        return self._new_connected_schools

    @property
    def totals_lookup_table_mil(self):
        return {
            "Technology CapEx": sum(self.output_cost_table["capex"]) / MILLION,
            "Electricity CapEx": sum(self.output_cost_table["electricity_capex"])
            / MILLION,
            "Annual Recurring Cost": sum(self.output_cost_table["recurring_costs"])
            / MILLION,
        }

    @property
    def averages_lookup_table_usd(self):
        return {
            "Cost per School": self.output_cost_table["total_cost"].mean(),
            "Cost per Student": self.output_cost_table["total_cost"].sum()
            / self.output_cost_table["num_students"].sum(),
        }

    @property
    def technology_counts(self):
        return dict(self.output_cost_table["technology"].value_counts())

    @property
    def average_mbps(self):
        return sum(
            [
                v * self.config.maximum_bandwidths[k]
                for k, v in self.technology_counts.items()
            ]
        ) / len(self.output_cost_table)

    @property
    def output_project_overview(self):
        current_connected_schools = self.complete_school_table["connected"].sum()
        new_connected_schools = self.output_cost_table["feasible"].sum()
        current_connected_students = self.complete_school_table["num_students"].sum()
        new_connected_students = self.output_cost_table["num_students"].sum()
        return ProjectOverview(
            total_students=self.complete_school_table["num_students"].sum(),
            total_schools=len(self.complete_school_table),
            schools_connected_current=current_connected_schools,
            schools_connected_projected=new_connected_schools
            + current_connected_schools,
            students_connected_current=current_connected_students,
            students_connected_projected=current_connected_students
            + new_connected_students,
            connected_percentage_current=round(
                current_connected_schools / len(self.complete_school_table) * 100
            ),
            connected_percentage_projected=round(
                (new_connected_schools + current_connected_schools)
                / len(self.complete_school_table)
                * 100
            ),
            average_mbps=round(self.average_mbps),
        )

    @property
    def unit_costs(self):
        def get_tech_config(techs, tech_name):
            for t in techs:
                if t.technology == tech_name:
                    return t
            raise ValueError(f"Technology {tech_name} not avaible")

        fiber_tech = get_tech_config(self.config.technologies, "Fiber")
        p2p_tech = get_tech_config(self.config.technologies, "P2P")
        leo_tech = get_tech_config(self.config.technologies, "Satellite")
        cell_tech = get_tech_config(self.config.technologies, "Cellular")
        return {
            "upfront": {
                "Fiber": {
                    "cost": fiber_tech.capex.cost_per_km,
                    "label": "Fiber ($/km ) ",
                },
                "P2P": {
                    "cost": p2p_tech.capex.fixed_costs + p2p_tech.capex.fixed_costs,
                    "label": "P2P ($/setup) ",
                },
                "LEOs": {
                    "cost": leo_tech.capex.fixed_costs,
                    "label": "LEOs ($/setup) ",
                },
                "Cellular": {
                    "cost": cell_tech.capex.fixed_costs,
                    "label": "Cellular ($/setup) ",
                },
            },
            "ongoing": {
                "Fiber": {
                    "cost": fiber_tech.opex.annual_bandwidth_cost_per_mbps,
                    "label": "Fiber ($/Mbps) ",
                },
                "P2P": {
                    "cost": p2p_tech.opex.annual_bandwidth_cost_per_mbps,
                    "label": "P2P ($/Mbps) ",
                },
                "LEOs": {
                    "cost": leo_tech.opex.annual_bandwidth_cost_per_mbps,
                    "label": "LEOs ($/Mbps) ",
                },
                "Cellular": {
                    "cost": cell_tech.opex.annual_bandwidth_cost_per_mbps,
                    "label": "Cellular ($/Mbps) ",
                },
            },
        }

    def get_cumulative_distance_fraction(self, distance, distance_key):
        return sum(self.output_cost_table[distance_key] <= distance) / len(
            self.output_cost_table
        )
