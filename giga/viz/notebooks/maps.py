from pydantic import BaseModel
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os

from giga.schemas.school import GigaSchoolTable
from giga.viz.notebooks.cost_estimation_parameter_input import CostEstimationParameterInput
from giga.data.stats.result_stats import ResultStats
from giga.viz.notebooks.data_maps.static_data_map import DataMapConfig
from giga.viz.notebooks.data_maps.map_data_layers import BaseDataLayerConfig
from giga.viz.colors import ELECTRICITY_AVAILABILITY_COLORS


MAP_BOX_ACCESS_TOKEN = os.environ.get("MAP_BOX_ACCESS_TOKEN", "")

class ResultMapConfig(BaseModel):

    width: int = 850
    height: int = 600
    style_default: str = "carto-darkmatter"
    style_mapbox: str = "dark"
    title_x: float = 0.5
    title_y: float = 0.95
    legend_x: float = 0.05
    legend_y: float = 0.95
    legend_bgcolor: str = "#262624"
    legend_width: str = 75  # px
    legend_font_color: str = "white"
    legend_border_color: str = "#070807"
    legend_border_width: int = 1
    no_cell: bool = False

class ElectricityMapLayerConfig(BaseDataLayerConfig):

    title: str = "Electricity Availability by School"
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = "Electricity Availability"
    color_map: list = ELECTRICITY_AVAILABILITY_COLORS

class CostMapLayerConfig(BaseDataLayerConfig):
    
    title: str = "Total Cost by School"
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = "School Cost Groups"
    color_map = px.colors.diverging.RdYlGn[::-1][2:]

class InfraLinesMapLayerConfig(BaseDataLayerConfig):
    title: str = 'Infrastructure Lines'
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = 'Infrastructure Lines'
    line_color: dict = {'fiber': 'orange', 'p2p': '#1f77b4'}
    line_width: float = 2

class ResultMapLayersConfig(BaseModel):

    electricity_layer: ElectricityMapLayerConfig = ElectricityMapLayerConfig()
    cost_layer: CostMapLayerConfig = CostMapLayerConfig()
    infra_lines_layer = InfraLinesMapLayerConfig = InfraLinesMapLayerConfig()

class ResultMap:
    
    def __init__(self, stats: ResultStats, inputs: CostEstimationParameterInput, map_config: ResultMapConfig, layer_config: ResultMapLayersConfig):
        self.stats = stats
        self.inputs = inputs
        self.data_space = stats.data_space
        self.config = map_config
        self.layer_config = layer_config
        self.country = inputs.data_parameters().school_data_conf.country_id
        self.country_zoom = inputs.defaults[self.country].data.country_zoom
        self.country_center = inputs.defaults[self.country].data.country_center_tuple
        
        self._schools = None
        self._fig = None
    
    @property 
    def schools(self):
        if self._schools is None:
            self._schools = self.get_school_dataframe()
        return self._schools
    
    @property
    def fig(self):
        if self._fig is None:
            self._fig = self.get_base_result_map()
        return self._fig
    
    def get_school_dataframe(self):
        return GigaSchoolTable(
            schools=self.data_space.school_entities
        ).to_data_frame()
    
    def get_base_result_map(self):
        
        fig = go.FigureWidget()
        
        style = (
            self.config.style_default
            if MAP_BOX_ACCESS_TOKEN == ""
            else self.config.style_mapbox
        )
        
        token = None if MAP_BOX_ACCESS_TOKEN == "" else MAP_BOX_ACCESS_TOKEN

        fig.update_layout(
            autosize = True,
            width=self.config.width,  # Adjust the width of the map
            height=self.config.height,  # Adjust the height of the map
            hovermode="closest",
            mapbox=dict(
                center=dict(lat=self.country_center[0], lon=self.country_center[1]),
                zoom=self.country_zoom,
                style=style,
                accesstoken=token,
                uirevision=False,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            hoverlabel=dict(font_size=9),
        )

        return fig

    

    def get_electricity_map(self):

        fig = go.FigureWidget(self.fig)

        schools_df = self.schools.copy()

        for electricity_availability in [True, False]:
            df = schools_df[schools_df['has_electricity'] == electricity_availability]

            fig.add_trace(
                go.Scattermapbox(
                    name = ('Yes' if electricity_availability else 'No'),
                    lat = df['lat'],
                    lon = df['lon'],
                    text = df['name'],
                    customdata=df["giga_id"],
                    mode="markers",
                    marker = go.scattermapbox.Marker(
                        size = self.layer_config.electricity_layer.marker_size,
                        color = ELECTRICITY_AVAILABILITY_COLORS[int(electricity_availability)],
                        opacity=self.layer_config.electricity_layer.marker_opacity
                    ),
                    hovertemplate="<b>Name:</b> %{text}<br><b>ID:</b> %{customdata}",
                )
            )
        
        fig.update_layout(
            showlegend=True,
            legend=dict(
                x=self.config.legend_x,
                y=self.config.legend_y,
                bgcolor=self.config.legend_bgcolor,
                font=dict(color=self.config.legend_font_color),
                bordercolor=self.config.legend_border_color,
                borderwidth=self.config.legend_border_width,
            ),
            title=dict(
                text = self.layer_config.electricity_layer.title,
                y= self.config.title_y,
                x= self.config.title_x,
                xanchor= "center",
                yanchor= "top",
                font= dict(
                    size=18, color="white", family="Verdana"
                ),
            )
        )

        return fig
    
    def get_cost_map(self):

        fig = go.FigureWidget(self.fig)

        df = self.stats.new_connected_schools

        fig.add_trace(
            go.Scattermapbox(
                lat = df['lat'],
                lon = df['lon'],
                text = df['total_cost'].map(lambda x: f'{x:,}'),
                customdata = np.stack((df['school_id'], df['technology']), axis=-1),
                mode='markers',
                marker = go.scattermapbox.Marker(
                    color = df['total_cost'],
                    colorscale=self.layer_config.cost_layer.color_map,
                    size = self.layer_config.cost_layer.marker_size,
                    opacity=self.layer_config.cost_layer.marker_opacity,
                    colorbar=dict(
                        xanchor="center",
                        yanchor="top",
                        x=.95,
                        y=1,
                        bgcolor=self.config.legend_bgcolor,
                        tickfont=dict(color=self.config.legend_font_color),
                        bordercolor=self.config.legend_border_color,
                        borderwidth=self.config.legend_border_width,
                        title = 'Total Cost (USD)',
                        titlefont = dict(color=self.config.legend_font_color),
                    ),
                ),
                hovertemplate="<b>Total cost:</b> %{text} USD<br><b>ID:</b> %{customdata[0]}<br><b>Technology:</b> %{customdata[1]}<extra></extra>",
            )
        )

        fig.update_layout(
            title=dict(
                text = self.layer_config.cost_layer.title,
                y= self.config.title_y,
                x= self.config.title_x,
                xanchor= "center",
                yanchor= "top",
                font= dict(
                    size=18, color="white", family="Verdana"
                ),
            )
        )

        return fig


    def get_infra_lines_map(self, data_map):
        
        connections_ = dict(
            fiber = self.stats.fiber_connections,
            p2p = self.stats.p2p_connections,
        )
        
        if (len(connections_['fiber']) + len(connections_['p2p']))==0:
            return None

        fig = go.FigureWidget(data_map)

        for tech_ in connections_.keys():

            lats = []
            lons = []
            texts = []

            for connection_ in connections_[tech_]:

                coordinate1_id, coordinate2_id = connection_.pair_ids
                coordinate1 = connection_.coordinate1.coordinate # lat, lon
                coordinate2 = connection_.coordinate2.coordinate

                lats += [coordinate1[0], coordinate2[0], None]
                lons += [coordinate1[1], coordinate2[1], None]
                texts += [coordinate1_id, coordinate2_id, None]
                
            fig.add_trace(
                go.Scattermapbox(
                    name = tech_.upper() + ' connection',
                    mode='lines',
                    lat=lats,
                    lon=lons,
                    text = texts,
                    line=dict(
                        width=self.layer_config.infra_lines_layer.line_width, 
                        color=self.layer_config.infra_lines_layer.line_color[tech_],
                    ),
                    showlegend = True,
                    hovertemplate="<b>ID:</b> %{text}",
                )
            )

        
        fig.update_layout(
            #hovermode = 'x unified',
            title=dict(
                text = self.layer_config.infra_lines_layer.title,
                y= self.config.title_y,
                x= self.config.title_x,
                xanchor= "center",
                yanchor= "top",
                font= dict(
                    size=18, color="white", family="Verdana"
                ),
            )
        )
    
        return fig

    def populate_result_maps(self):

        self.electricity_map = self.get_electricity_map()
        self.cost_map = self.get_cost_map()
        self.infra_lines_map = self.get_infra_lines_map(data_map = self.inputs.selected_data_map())
    
    def get_result_maps(self):
        try:
            return [
                self.electricity_map,
                self.cost_map,
                self.infra_lines_map,
            ]
        except:
            self.populate_result_maps()
            return [
                self.electricity_map,
                self.cost_map,
                self.infra_lines_map,
            ]
