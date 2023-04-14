from pydantic import BaseModel
import plotly.graph_objs as go
import pandas as pd

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.school import GigaSchoolTable


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
    def cell_tower_layer(self):
        """
        Returns a scattermapbox object for the cell towers in the data space
        """
        if self._cell_towers is None:
            cell = pd.DataFrame(
                [cc.dict() for cc in self.data_space.cell_tower_coordinates]
            )
            cell["lat"] = cell["coordinate"].apply(lambda x: x[0])
            cell["lon"] = cell["coordinate"].apply(lambda x: x[1])
            self._cell_towers = cell
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
    def fiber_layer(self):
        """
        Returns a scattermapbox object for the fiber nodes in the data space
        """
        if self._fiber_nodes is None:
            fiber = pd.DataFrame(
                [fc.dict() for fc in self.data_space.fiber_coordinates]
            )
            fiber["lat"] = fiber["coordinate"].apply(lambda x: x[0])
            fiber["lon"] = fiber["coordinate"].apply(lambda x: x[1])
            self._fiber_nodes = fiber
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
    def layers(self):
        """
        Returns a list of all the data layers
        """
        return [self.school_layer, self.cell_tower_layer, self.fiber_layer]
