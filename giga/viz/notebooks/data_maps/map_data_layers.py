import os
from pydantic import BaseModel
import plotly.graph_objs as go
import pandas as pd
from typing import List, Dict

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.school import GigaSchoolTable


MAP_BOX_ACCESS_TOKEN = os.environ.get("MAP_BOX_ACCESS_TOKEN", "")


class BaseDataLayerConfig(BaseModel):

    marker_size: int  # in pixels
    marker_color: str
    marker_opacity: float
    layer_name: str


class SchoolMapLayerConfig(BaseDataLayerConfig):

    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = "School"
    ordered_status: List[str] = ["Unknown", "No connection", "Moderate", "Good"]
    color_map: Dict[str, str] = {
        "Good": "#8bd431",
        "Moderate": "#ffc93d",
        "No connection": "#ff615b",
        "Unknown": "#556fc2",
    }


class CellTowerMapLayerConfig(BaseDataLayerConfig):

    marker_size: int = 7
    marker_color: str = "#48cae4"
    marker_opacity: float = 0.85
    layer_name: str = "Cell Tower"


class FiberMapLayerConfig(BaseDataLayerConfig):

    marker_size: int = 10
    marker_color: str = "#ffc300"
    marker_opacity: float = 0.85
    layer_name: str = "Fiber Node"


class MapLayersConfig(BaseModel):

    school_layer: SchoolMapLayerConfig = SchoolMapLayerConfig()
    cell_tower_layer: CellTowerMapLayerConfig = CellTowerMapLayerConfig()
    fiber_layer = FiberMapLayerConfig = FiberMapLayerConfig()


class MapDataLayers:
    """
    This class is responsible for generating the data layers for the maps used in the app.
    """

    def __init__(self, data_space: ModelDataSpace, config: MapLayersConfig):
        self.data_space = data_space
        self.config = config
        self._schools = None
        self._cell_towers = None
        self._fiber_nodes = None

    @property
    def school_layer(self):
        """
        Returns a scattermapbox object for the schools in the data space
        """
        if self._schools is None:
            self._schools = GigaSchoolTable(
                schools=self.data_space.school_entities
            ).to_data_frame()
        return go.Scattermapbox(
            name=self.config.school_layer.layer_name,
            lon=self._schools["lon"],
            lat=self._schools["lat"],
            text=self._schools["name"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=self.config.school_layer.marker_size,
                color=self.config.school_layer.marker_color,
                opacity=self.config.school_layer.marker_opacity,
            ),
        )

    @property
    def school_layers_mb(self):
        """
        Returns a scattermapbox object for the schools in the data space
        """
        if self._schools is None:
            self._schools = self.data_space.all_schools.to_data_frame()
        layers = []
        for status in reversed(self.config.school_layer.ordered_status):
            ff = self._schools[self._schools["connectivity_status"] == status]
            l = go.Scattermapbox(
                name=status,
                lon=ff["lon"],
                lat=ff["lat"],
                text=ff["name"],
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=self.config.school_layer.marker_size,
                    color=self.config.school_layer.color_map[status],
                    opacity=self.config.school_layer.marker_opacity,
                ),
            )
            layers.append(l)
        return layers

    @property
    def cell_tower_layer(self):
        """
        Returns a scattermapbox object for the cell towers in the data space
        """
        if self._cell_towers is None:
            self._cell_towers = self.data_space.cell_tower_map.to_data_frame()
        return go.Scattermapbox(
            name=self.config.cell_tower_layer.layer_name,
            lon=self._cell_towers["lon"],
            lat=self._cell_towers["lat"],
            text=self._cell_towers["coordinate_id"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=self.config.cell_tower_layer.marker_size,
                color=self.config.cell_tower_layer.marker_color,
                opacity=self.config.cell_tower_layer.marker_opacity,
            ),
        )

    @property
    def cell_tower_layer_mb(self):
        if self._cell_towers is None:
            self._cell_towers = self.data_space.cell_tower_map.to_data_frame()
        return go.Scattermapbox(
            name="Cell Tower",
            lon=self._cell_towers["lon"],
            lat=self._cell_towers["lat"],
            text=self._cell_towers["coordinate_id"],
            mode="markers",
            showlegend=False,
            marker=go.scattermapbox.Marker(
                symbol="square", size=3, color="gray", opacity=1, allowoverlap=True
            ),
        )

    @property
    def cell_tower_layer_mb_empty(self):
        if self._cell_towers is None:
            self._cell_towers = self.data_space.cell_tower_map.to_data_frame()
        return go.Scattermapbox(
            name="Cell Tower",
            lon=[None],
            lat=[None],
            mode="markers",
            showlegend=False,
            marker=go.scattermapbox.Marker(
                symbol="square", size=3, color="gray", opacity=1, allowoverlap=True
            ),
        )

    @property
    def cell_tower_layer_mb_legend(self):
        return go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Cell Tower",
            marker=dict(size=8, color="#b4b5b8", symbol="square"),
        )

    @property
    def fiber_layer(self):
        """
        Returns a scattermapbox object for the fiber nodes in the data space
        """
        if self._fiber_nodes is None:
            self._fiber_nodes = self.data_space.fiber_map.to_data_frame()
        return go.Scattermapbox(
            name=self.config.fiber_layer.layer_name,
            lon=self._fiber_nodes["lon"],
            lat=self._fiber_nodes["lat"],
            text=self._fiber_nodes["coordinate_id"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=self.config.fiber_layer.marker_size,
                color=self.config.fiber_layer.marker_color,
                opacity=self.config.fiber_layer.marker_opacity,
            ),
        )

    @property
    def fiber_layer_mb(self):
        if self._fiber_nodes is None:
            self._fiber_nodes = self.data_space.fiber_map.to_data_frame()
        return go.Scattermapbox(
            name="Fiber Node",
            lon=self._fiber_nodes["lon"],
            lat=self._fiber_nodes["lat"],
            text=self._fiber_nodes["coordinate_id"],
            mode="markers",
            showlegend=False,
            marker=go.scattermapbox.Marker(
                symbol="triangle", size=7, color="gray", opacity=1, allowoverlap=True
            ),
        )

    @property
    def fiber_layer_mb_legend(self):
        return go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Fiber Node",
            marker=dict(size=8, color="#b4b5b8", symbol="triangle-up"),
        )

    @property
    def layers(self):
        """
        Returns a list of all the data layers
        """
        if MAP_BOX_ACCESS_TOKEN == "":
            return self._layers
        else:
            return self._layers_mapbox

    @property
    def layers_no_cell(self):
        """
        Returns a list of data layers without the cell tower layer
        """
        if MAP_BOX_ACCESS_TOKEN == "":
            return [self.school_layer, self.fiber_layer]
        else:
            return [
                self.fiber_layer_mb,
                self.fiber_layer_mb_legend,
            ] + self.school_layers_mb

    @property
    def _layers(self):
        """
        Returns a list of all the data layers
        """
        return [self.school_layer, self.cell_tower_layer, self.fiber_layer]

    @property
    def _layers_mapbox(self):
        """
        Returns a list of all the data layers for mapbox tiles
        """
        return (
            [self.cell_tower_layer_mb, self.cell_tower_layer_mb_legend]
            + [self.fiber_layer_mb, self.fiber_layer_mb_legend]
            + self.school_layers_mb
        )
