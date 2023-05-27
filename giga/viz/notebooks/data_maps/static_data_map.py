import os
from typing import List, Dict
from pydantic import BaseModel
import plotly.graph_objs as go
import plotly.io as pio
from ipywidgets import Layout, VBox, HTML


from giga.data.space.model_data_space import ModelDataSpace
from giga.viz.notebooks.data_maps.selection_map_data_layers import (
    SelectionMapDataLayers,
)
from giga.viz.notebooks.components.html.sections import section


MAP_BOX_ACCESS_TOKEN = os.environ.get("MAP_BOX_ACCESS_TOKEN", "")


STATIC_MAP_MODEBAR_CONFIG = {
    'displayModeBar': "hover",
    'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'],
    'toImageButtonOptions': {
        'format': 'jpeg', # one of png, svg, jpeg, webp
        'filename': 'custom_image',
        'height': 1200,
        'width': 1200,
    },
    'displaylogo': False
}

SELECTION_MAP_MODEBAR_CONFIG = {
    'displayModeBar': True,
    'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'],
    'toImageButtonOptions': {
        'format': 'jpeg', # one of png, svg, jpeg, webp
        'filename': 'custom_image',
        'height': 1200,
        'width': 1200,
    },
    'displaylogo': False
}

class ModeBarConfig(BaseModel):
    image_button_config: dict = {
        "format": "svg",  # one of png, svg, jpeg, webp
        "filename": "custom_image",
        "height": 500,
        "width": 700,
        "scale": 1,  # Multiply title/legend/axis/canvas sizes by this factor
    }
    displayModeBar: bool = True
    displaylogo: bool = False

    @property
    def config(self):
        return {"toImageButtonOptions": self.image_button_config}

    def set_jupyterlab(self):
        pio.renderers["jupyterlab"].config["displayModeBar"] = self.displayModeBar
        pio.renderers["jupyterlab"].config["displaylogo"] = self.displaylogo


class DataMapConfig(BaseModel):

    width: int = 850
    height: int = 600
    zoom: int = 7
    style_default: str = "carto-darkmatter"
    style_mapbox: str = "dark"
    legend_x: float = 0.05
    legend_y: float = 0.95
    legend_bgcolor: str = "#262624"
    legend_width: str =  75 # px
    legend_font_color: str = "white"
    legend_border_color: str = "#070807"
    legend_border_width: int = 1
    mode_bar_config: ModeBarConfig = ModeBarConfig()
    jupyterlab: bool = True
    no_cell: bool = False


class StaticDataMap:
    def __init__(self, config: DataMapConfig):
        self.config = config
        if self.config.jupyterlab:
            self.config.mode_bar_config.set_jupyterlab()
        self.fig = go.FigureWidget()

    def add_layer(self, layer: go.Scattermapbox):
        self.fig.add_trace(layer)

    def add_layers(self, layers: List[go.Scattermapbox]):
        for l in layers:
            l.name = l.name + "   "
            self.add_layer(l)

    def get_map(self, center: List[float], infra_toggle=True, **kwargs):
        style = (
            self.config.style_default
            if MAP_BOX_ACCESS_TOKEN == ""
            else self.config.style_mapbox
        )
        token = None if MAP_BOX_ACCESS_TOKEN == "" else MAP_BOX_ACCESS_TOKEN
        update_menu = []
        if infra_toggle:
            update_menu = [
                    go.layout.Updatemenu(
                        bgcolor='#474747', # This changes the background color to a dark gray
                        font=dict(color='white'),
                        buttons=list([
                            dict(
                                args=[{"visible": [True]}],
                                label="Show all",
                                method="update"
                            ),
                            dict(
                                args=[{"visible": [False, False, False, False, True, True, True, True]}],
                                label=" Hide Infrastructure ",
                                method="update"
                            ),
                        ]),
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.75,
                    xanchor="left",
                    y=0.95,
                    yanchor="top"
                ),
            ]
        self.fig.update_layout(
            autosize=True,
            width=self.config.width,  # Adjust the width of the map
            height=self.config.height,  # Adjust the height of the map
            hovermode="closest",
            updatemenus=update_menu,
            mapbox=dict(
                center=dict(lat=center[0], lon=center[1]),
                zoom=self.config.zoom,
                style=style,
                accesstoken=token,
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
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            **kwargs,
        )
        return self.fig

    def get_selection_map(
        self, center: List[float], layers: SelectionMapDataLayers, **kwargs
    ):
        l = layers.layers_selection_no_cell if self.config.no_cell else layers.layers_selection
        self.add_layers(l)
        m = self.get_map(center, infra_toggle=False)
        layers.connect_school_layer_selection(m)
        layout = Layout()  # add centering and other formatting here
        return VBox([
            m, 
            HTML("<br/>"),
            section("Current Selections", layers.school_selection_table, "nopad")], layout=layout)
