from typing import List
from pydantic import BaseModel
import plotly.graph_objs as go


from giga.data.space.model_data_space import ModelDataSpace


class DataMapConfig(BaseModel):

    width: int = 1050
    height: int = 600
    zoom: int = 7
    style: str = "carto-darkmatter"
    legend_x: float = 0.05
    legend_y: float = 0.95
    legend_bgcolor: str = "#262624"
    legend_font_color: str = "white"
    legend_border_color: str = "#070807"
    legend_border_width: int = 1


class StaticDataMap:
    def __init__(self, config: DataMapConfig):
        self.config = config
        self.fig = go.Figure()

    def add_layer(self, layer: go.Scattermapbox):
        self.fig.add_trace(layer)

    def add_layers(self, layers: List[go.Scattermapbox]):
        for l in layers:
            self.add_layer(l)

    def get_map(self, center: List[float], **kwargs):
        self.fig.update_layout(
            autosize=False,
            width=self.config.width,  # Adjust the width of the map
            height=self.config.height,  # Adjust the height of the map
            hovermode="closest",
            mapbox=dict(
                center=dict(lat=center[0], lon=center[1]),
                zoom=self.config.zoom,
                style=self.config.style,
                uirevision=False,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True,
            legend=dict(
                x=self.config.legend_x,
                y=self.config.legend_y,
                bgcolor=self.config.legend_bgcolor,
                font=dict(color=self.config.legend_font_color),
                bordercolor=self.config.legend_border_color,
                borderwidth=self.config.legend_border_width,
            ),
            **kwargs,
        )
        return self.fig
