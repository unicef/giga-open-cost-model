import os
from pydantic import BaseModel
import plotly.graph_objs as go
import pandas as pd
from typing import List, Dict

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.school import GigaSchoolTable
from giga.viz.notebooks.data_maps.map_data_layers import MapDataLayers, MapLayersConfig


MAP_BOX_ACCESS_TOKEN = os.environ.get("MAP_BOX_ACCESS_TOKEN", "")


class SelectionMapLayersConfig(MapLayersConfig):

    allow_connected_schools: bool = (
        False  # wether schools that are already connected can be selected
    )
    table_headers: List[str] = ["Giga ID", "Name", "Connectivity", "Electricity"]
    table_data_columns: List[str] = [
        "giga_id",
        "name",
        "connectivity_status",
        "has_electricity",
    ]
    table_column_widths: List[float] = [1.25, 1, 1, 1]
    first_school_data_layer: str = "Good"  # connectivity quality


class SelectionMapDataLayers(MapDataLayers):
    """
    This class is responsible for generating data layers for selection maps in the app
    """

    def __init__(self, data_space: ModelDataSpace, config: SelectionMapLayersConfig):
        super().__init__(
            data_space, config
        )  # if the parent class has an __init__ method
        self._schools = (
            self.data_space.all_schools.to_data_frame()
            if config.allow_connected_schools
            else GigaSchoolTable(
                schools=self.data_space.school_entities
            ).to_data_frame()
        )
        self._school_table_selector = None
        self._layers_selection = None
        self._layers_selection_no_cell = None

    @staticmethod
    def from_loaded_data_layers(
        config: SelectionMapLayersConfig, layers: MapDataLayers
    ):
        selection_layers = SelectionMapDataLayers(layers.data_space, config)
        selection_layers._cell_towers = layers._cell_towers
        selection_layers._fiber_nodes = layers._fiber_nodes
        return selection_layers

    @property
    def school_selection_table(self):
        if self._school_table_selector is None:
            self._school_table_selector = go.FigureWidget(
                [
                    go.Table(
                        header=dict(
                            values=self.config.table_headers,
                            fill=dict(color="#d6e4fd"),
                            align=["left"] * 5,
                        ),
                        columnwidth=self.config.table_column_widths,
                        cells=dict(
                            values=[
                                self._schools[col]
                                for col in self.config.table_data_columns
                            ],
                            fill=dict(color="#f5f5f5"),
                            align=["left"] * 5,
                        ),
                    )
                ]
            )
        return self._school_table_selector

    def connect_school_layer_selection(self, fig):
        def selection_fn(trace, points, selector):
            point_inds = list(points.point_inds)
            status = trace.name
            filtered_schools = self._schools[
                self._schools["connectivity_status"] == trace.name
            ].reset_index()
            if status == self.config.first_school_data_layer:
                # first trace in selection
                self.school_selection_table.data[0].cells.values = [
                    filtered_schools.loc[point_inds][col]
                    for i, col in enumerate(self.config.table_data_columns)
                ]
            else:
                values = []
                for i, col in enumerate(self.config.table_data_columns):
                    vc = self.school_selection_table.data[0].cells.values[i] + list(
                        filtered_schools.loc[point_inds][col]
                    )
                    values.append(vc)
                self.school_selection_table.data[0].cells.values = values

        for scatter in fig.data[4:8]:
            scatter.on_selection(selection_fn)

    @property
    def layers_selection(self):
        if self._layers_selection is None:
            self._layers_selection = [
                self.fiber_layer_mb,
                self.cell_tower_layer_mb,
                self.cell_tower_layer_mb_legend,
                self.fiber_layer_mb_legend,
            ] + self.school_layers_mb
        return self._layers_selection

    @property
    def layers_selection_no_cell(self):
        if self._layers_selection is None:
            self._layers_selection = [
                self.fiber_layer_mb,
                self.cell_tower_layer_mb_empty,
                self.cell_tower_layer_mb_legend,
                self.fiber_layer_mb_legend,
            ] + self.school_layers_mb
        return self._layers_selection

    @property
    def selected_schools(self):
        return self.school_selection_table.data[0].cells.values[0]
