from pydantic import BaseModel
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict
import os

from giga.app.config import get_country_center_zoom
from giga.schemas.school import GigaSchoolTable
from giga.viz.notebooks.cost_estimation_parameter_input import CostEstimationParameterInput, LARGE_COUNTRIES
from giga.data.stats.result_stats import ResultStats
from giga.viz.notebooks.data_maps.static_data_map import DataMapConfig
from giga.viz.notebooks.data_maps.map_data_layers import MapDataLayers, BaseDataLayerConfig, MapLayersConfig
from giga.viz.colors import ELECTRICITY_AVAILABILITY_COLORS, GIGA_TECHNOLOGY_COLORS, FIBER_COLORBAR_MIN, FIBER_COLORBAR_MAX, CELLULAR_COLORBAR_MIN, CELLULAR_COLORBAR_MAX, CELL_COVERAGE_COLOR_MAP


MAPBOX_ACCESS_TOKEN = os.environ.get("MAP_BOX_ACCESS_TOKEN", "")

class CostMapLayerConfig(BaseDataLayerConfig):
    
    title: str = "Total Cost by School"
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = "School Cost Groups"
    color_map = px.colors.diverging.RdYlGn[::-1][2:]

class TechnologyMapLayerConfig(BaseDataLayerConfig):

    title: str = 'Unconnected Schools - Modality to Connect'
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: float = 'Technology Connected'
    color_map = GIGA_TECHNOLOGY_COLORS

class InfraLinesMapLayerConfig(BaseDataLayerConfig):
    title: str = 'Infrastructure Lines'
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = 'Infrastructure Lines'
    line_color: dict = {'fiber': 'rgba(169, 39, 255, .5)', 'p2p': 'rgba(39, 255, 161, .5)'}
    line_width: float = 2

class FiberDistMapLayerConfig(BaseDataLayerConfig):
    key: str = 'nearest_fiber'
    title: str = 'Unconnected School Proximity to Fiber Nodes'
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = 'Nearest Fiber Distance'
    color_map = 'Spectral_r'
    color_max = FIBER_COLORBAR_MAX
    color_min = FIBER_COLORBAR_MIN
    colorbar_title = 'Nearest fiber (km)'
    hovertemplate="<b>ID:</b> %{customdata}<br><b>Fiber node distance:</b> %{text} km<extra></extra>"

class CellDistMapLayerConfig(BaseDataLayerConfig):
    key: str = 'nearest_cell_tower'
    title: str = 'Unconnected School Proximity to Cell Towers'
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = 'Nearest Cell Tower Distance'
    color_map = 'Spectral_r'
    color_max = CELLULAR_COLORBAR_MAX
    color_min = CELLULAR_COLORBAR_MIN
    colorbar_title = 'Nearest cell tower (km)'
    hovertemplate="<b>ID:</b> %{customdata}<br><b>Cell tower distance:</b> %{text} km<extra></extra>"

class P2PDistMapLayerConfig(BaseDataLayerConfig):
    key: str = 'nearest_visible_cell_tower'
    title: str = 'Unconnected School Proximity to Visible Cell Towers'
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = 'Nearest Visible Cell Tower Distance'
    color_map = 'Spectral_r'
    color_max = CELLULAR_COLORBAR_MAX
    color_min = CELLULAR_COLORBAR_MIN
    colorbar_title = 'Nearest visible cell tower (km)'
    hovertemplate="<b>ID:</b> %{customdata}<br><b>Visible cell tower distance:</b> %{text} km<extra></extra>"

class CellCoverageMapLayerConfig(BaseDataLayerConfig):

    title: str = "Cellular Coverage"
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = "Cellular Coverage"
    color_map: list = CELL_COVERAGE_COLOR_MAP


class ElectricityMapLayerConfig(BaseDataLayerConfig):

    title: str = "Electricity Availability"
    marker_size: int = 5
    marker_color: str = "#9f86c0"
    marker_opacity: float = 0.95
    layer_name: str = "Electricity Availability"
    color_map: list = ELECTRICITY_AVAILABILITY_COLORS

class ResultMapLayersConfig(BaseModel):

    cost_layer: CostMapLayerConfig = CostMapLayerConfig()
    tech_layer: TechnologyMapLayerConfig = TechnologyMapLayerConfig()
    infra_lines_layer: InfraLinesMapLayerConfig = InfraLinesMapLayerConfig()
    fiber_dist_layer: FiberDistMapLayerConfig = FiberDistMapLayerConfig()
    cell_tower_dist_layer: CellDistMapLayerConfig = CellDistMapLayerConfig()
    p2p_dist_layer: P2PDistMapLayerConfig = P2PDistMapLayerConfig()
    cell_coverage_layer: CellCoverageMapLayerConfig = CellCoverageMapLayerConfig()
    electricity_layer: ElectricityMapLayerConfig = ElectricityMapLayerConfig()

class InfraMapLayersConfig(BaseModel):

    fiber_dist_layer: FiberDistMapLayerConfig = FiberDistMapLayerConfig()
    cell_tower_dist_layer: CellDistMapLayerConfig = CellDistMapLayerConfig()
    p2p_dist_layer: P2PDistMapLayerConfig = P2PDistMapLayerConfig()
    cell_coverage_layer: CellCoverageMapLayerConfig = CellCoverageMapLayerConfig()
    electricity_layer: ElectricityMapLayerConfig = ElectricityMapLayerConfig()

class InfraMap:

    def __init__(self, data_space, map_config: DataMapConfig, layer_config: InfraMapLayersConfig):
        self.data_space = data_space
        self.config = map_config
        self.layer_config = layer_config

        self._all_schools = None
        self._schools = None
        self._fig = None
        self._infra_maps = None

        self._fiber_dist_map = None
        self._cell_tower_dist_map = None
        self._p2p_dist_map = None
        self._cell_coverage_map = None
        self._electricity_map = None
    
    @property
    def all_schools(self):
        if self._all_schools is None:
            self._all_schools = self.data_space.schools_to_frame()
        return self._all_schools
    
    @property 
    def schools(self):
        if self._schools is None:
            self._schools = self.all_schools[self.all_schools['connected']==False]
        return self._schools

    @property
    def fig(self):
        if self._fig is None:
            _center, _zoom =  get_country_center_zoom(self.all_schools, max_zoom_level=11.5)
            self._fig = self.base_map(map_center=[_center['lat'], _center['lon']], map_zoom = _zoom)
        return self._fig
    
    @property
    def infra_maps(self):
        if self._infra_maps is None:
            self._infra_maps = dict(
                iber_dist_map = self.fiber_dist_map,
                cell_tower_dist_map = self.cell_tower_dist_map,
                p2p_dist_map = self.p2p_dist_map,
                cell_coverage_map = self.cell_coverage_map,
                electricity_map = self.electricity_map,
            )
        return self._infra_maps

    @property
    def fiber_dist_map(self):
        if self._fiber_dist_map is None:
            fig = go.FigureWidget(self.fig)

            fig.add_trace(
                self._distance_layer(df = self.schools, dist_layer_config=self.layer_config.fiber_dist_layer)
            )

            fig.update_layout(
                showlegend = False,
                title = dict(text = f'<b>{self.layer_config.fiber_dist_layer.title}')
            )
            self._fiber_dist_map = fig
        return self._fiber_dist_map
    
    @property
    def cell_tower_dist_map(self):
        if self._cell_tower_dist_map is None:
            fig = go.FigureWidget(self.fig)

            fig.add_trace(
                self._distance_layer(df = self.schools, dist_layer_config=self.layer_config.cell_tower_dist_layer)
            )

            fig.update_layout(
                showlegend = False,
                title = dict(text = f'<b>{self.layer_config.cell_tower_dist_layer.title}')
            )
            self._cell_tower_dist_map = fig
        return self._cell_tower_dist_map
     
    @property
    def p2p_dist_map(self):
        if self._p2p_dist_map is None:
            fig = go.FigureWidget(self.fig)

            fig.add_trace(
                self._distance_layer(df = self.schools, dist_layer_config=self.layer_config.p2p_dist_layer)
            )

            fig.update_layout(
                showlegend = False,
                title = dict(text = f'<b>{self.layer_config.p2p_dist_layer.title}')
            )
            self._p2p_dist_map = fig
        return self._p2p_dist_map
    
    @property
    def cell_coverage_map(self):
        if self._cell_coverage_map is None:
            fig = go.FigureWidget(self.fig)

            for l in self.cell_coverage_layers(df=self.schools):
                fig.add_trace(l)
            
            fig.update_layout(
                showlegend = True,
                title = dict(text = f'<b>{self.layer_config.cell_coverage_layer.title}')
            )
            self._cell_coverage_map = fig
        return self._cell_coverage_map

    
    @property
    def electricity_map(self):
        if self._electricity_map is None:
            fig = go.FigureWidget(self.fig)

            for l in self.electricity_layers(df = self.schools):
                fig.add_trace(l)
            
            fig.update_layout(
                showlegend = True,
                title = dict(text = f'<b>{self.layer_config.electricity_layer.title}')
            )
            self._electricity_map = fig
        return self._electricity_map
    
    def base_map(self, map_center, map_zoom):
        
        fig = go.FigureWidget()
        
        style = (
            self.config.style_default
            if MAPBOX_ACCESS_TOKEN == ""
            else self.config.style_mapbox
        )
        
        token = None if MAPBOX_ACCESS_TOKEN == "" else MAPBOX_ACCESS_TOKEN

        fig.update_layout(
            autosize = True,
            width=self.config.width,  # Adjust the width of the map
            height=self.config.height,  # Adjust the height of the map
            hovermode="closest",
            mapbox=dict(
                center=dict(lat=map_center[0], lon=map_center[1]),
                zoom=map_zoom,
                style=style,
                accesstoken=token,
                uirevision=False,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            hoverlabel=dict(font_size=9),
            title=dict(
                y= self.config.title_y,
                x= self.config.title_x,
                xanchor= "center",
                yanchor= "top",
                font= dict(
                    size=18, color="white", family="Verdana"
                ),
            ),
            showlegend=False,
            legend=dict(
                x=self.config.legend_x,
                y=self.config.legend_y,
                bgcolor=self.config.legend_bgcolor,
                font=dict(color=self.config.legend_font_color),
                bordercolor=self.config.legend_border_color,
                borderwidth=self.config.legend_border_width,
            ),
        )

        return fig
    
    def _distance_layer(self, df, dist_layer_config: BaseDataLayerConfig):

        df = df.copy()

        df['values'] = df[dist_layer_config.key].map(lambda x: np.round(x/1000, 2))

        l = go.Scattermapbox(
            lon = df['lon'],
            lat = df['lat'],
            text = df['values'],
            customdata = df['school_id'],
            mode='markers',
            marker = go.scattermapbox.Marker(
                color = df['values'],
                colorscale = dist_layer_config.color_map,
                size = dist_layer_config.marker_size,
                opacity=dist_layer_config.marker_opacity,
                cmax = dist_layer_config.color_max,
                cmin = dist_layer_config.color_min,
                colorbar=dict(
                    xanchor="left",
                    yanchor="top",
                    x=0,
                    y=1,
                    tickfont=dict(color=self.config.legend_font_color),
                    title = 'Nearest fiber (km)',
                    titlefont = dict(color=self.config.legend_font_color),
                ),
            ),
            hovertemplate=dist_layer_config.hovertemplate,
        )

        return l

    def cell_coverage_layers(self, df):

        layers = []

        for type_, color_ in self.layer_config.cell_coverage_layer.color_map.items():

            ff = df[df['cell_coverage_type'] == type_]

            l = go.Scattermapbox(
                name = type_,
                lat = ff['lat'],
                lon = ff['lon'],
                customdata=ff["school_id"],
                mode="markers",
                marker = go.scattermapbox.Marker(
                    size = self.layer_config.cell_coverage_layer.marker_size,
                    color = color_,
                    opacity=self.layer_config.cell_coverage_layer.marker_opacity
                ),
                hovertemplate="<b>ID:</b> %{customdata}",
            )

            layers.append(l)
        
        return layers

    def electricity_layers(self, df):

        layers = []

        for electricity_availability in [True, False]:
            ff = df[df['has_electricity'] == electricity_availability]

            layers.append(
                go.Scattermapbox(
                    name = ('Yes' if electricity_availability else 'No'),
                    lat = ff['lat'],
                    lon = ff['lon'],
                    customdata=ff["school_id"],
                    mode="markers",
                    marker = go.scattermapbox.Marker(
                        size = self.layer_config.electricity_layer.marker_size,
                        color = ELECTRICITY_AVAILABILITY_COLORS[int(electricity_availability)],
                        opacity=self.layer_config.electricity_layer.marker_opacity
                    ),
                    hovertemplate="<b>ID:</b> %{customdata}",
                )
            )

        return layers
    

class ResultMap:
    
    def __init__(self, stats: ResultStats, map_config: DataMapConfig, layer_config: ResultMapLayersConfig):
        self.stats = stats
        self.data_space = stats.data_space
        self.config = map_config
        self.layer_config = layer_config
        self.map_data_layers = MapDataLayers(data_space=self.data_space, config=MapLayersConfig())
        self.infra_map = InfraMap(data_space=self.data_space, map_config = map_config, layer_config=InfraMapLayersConfig())
        
        self._fiber_schools = None
        self._new_connected_schools = None
        self._fig = None
        self._result_maps = None

        # maps
        self._cost_map = None
        self._technology_map = None
        self._infra_lines_map = None
        self._fiber_dist_map = None
        self._cell_tower_dist_map = None
        self._p2p_dist_map = None
        self._cell_coverage_map = None
    
    @property
    def new_connected_schools(self):
        if self._new_connected_schools is None:
            self._new_connected_schools = self.stats.new_connected_schools
        return self._new_connected_schools
    
    @property
    def fiber_schools(self):
        if self._fiber_schools is None:
            self._fiber_schools = self.infra_map.all_schools[self.infra_map.all_schools['has_fiber'] == True]
        return self._fiber_schools
    
    @property
    def fig(self):
        if self._fig is None:
            self._fig = self.infra_map.fig
        return self._fig
    
    @property
    def result_maps(self):
        if self._result_maps is None:
            self._result_maps = dict(
                cost_map = self.cost_map,
                technology_map = self.technology_map,
                infra_lines_map = self.infra_lines_map,
                fiber_dist_map = self.fiber_dist_map,
                cell_tower_dist_map = self.cell_tower_dist_map,
                p2p_dist_map = self.p2p_dist_map,
                cell_coverage_map = self.cell_coverage_map,
            )
        return self._result_maps
    
    @property
    def cost_map(self):
        if self._cost_map is None:
            fig = go.FigureWidget(self.fig)
            
            fig.add_trace(self.total_cost_layer())

            fig.update_layout(
                showlegend = False,
                title = dict(text = f'<b>{self.layer_config.cost_layer.title}')
            )
            self._cost_map = fig
        return self._cost_map
    
    @property
    def technology_map(self):
        if self._technology_map is None:
            fig = go.FigureWidget(self.fig)

            for l in self.tech_connection_layers():
                fig.add_trace(l)
            
            fig.update_layout(
                showlegend = True,
                title = dict(text = f'<b>{self.layer_config.tech_layer.title}')
            )
            self._technology_map = fig
        return self._technology_map
    
    @property
    def infra_lines_map(self):
        if self._infra_lines_map is None:
            fig = go.FigureWidget(self.fig)

            for l in self.infra_lines_layers():
                fig.add_trace(l)
            
            fig.update_layout(
                showlegend = True,
                title =  f'<b>{self.layer_config.infra_lines_layer.title}'
            )
            self._infra_lines_map = fig
        return self._infra_lines_map

    @property
    def fiber_dist_map(self):
        if self._fiber_dist_map is None:
            fig = go.FigureWidget(self.fig)

            fig.add_trace(
                self.infra_map._distance_layer(df = self.new_connected_schools, dist_layer_config=self.layer_config.fiber_dist_layer)
            )

            fig.update_layout(
                showlegend = False,
                title = dict(text = f'<b>{self.layer_config.fiber_dist_layer.title}')
            )
            self._fiber_dist_map = fig
        return self._fiber_dist_map
    
    @property
    def cell_tower_dist_map(self):
        if self._cell_tower_dist_map is None:
            fig = go.FigureWidget(self.fig)

            fig.add_trace(
                self.infra_map._distance_layer(df = self.new_connected_schools, dist_layer_config=self.layer_config.cell_tower_dist_layer)
            )

            fig.update_layout(
                showlegend = False,
                title = dict(text = f'<b>{self.layer_config.cell_tower_dist_layer.title}')
            )
            self._cell_tower_dist_map = fig
        return self._cell_tower_dist_map
    
    @property
    def p2p_dist_map(self):
        if self._p2p_dist_map is None:
            fig = go.FigureWidget(self.fig)

            fig.add_trace(
                self.infra_map._distance_layer(df = self.new_connected_schools, dist_layer_config=self.layer_config.p2p_dist_layer)
            )

            fig.update_layout(
                showlegend = False,
                title = dict(text = f'<b>{self.layer_config.p2p_dist_layer.title}')
            )
            self._p2p_dist_map = fig
        return self._p2p_dist_map
    
    @property
    def cell_coverage_map(self):
        if self._cell_coverage_map is None:
            fig = go.FigureWidget(self.fig)

            for l in self.infra_map.cell_coverage_layers(df=self.new_connected_schools):
                fig.add_trace(l)
            
            fig.update_layout(
                showlegend = True,
                title = dict(text = f'<b>{self.layer_config.cell_coverage_layer.title}')
            )
            self._cell_coverage_map = fig
        return self._cell_coverage_map

    
    def total_cost_layer(self):

        df = self.new_connected_schools.copy()

        l = go.Scattermapbox(
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
                        xanchor="left",
                        yanchor="top",
                        x=0,
                        y=1,
                        tickfont=dict(color=self.config.legend_font_color),
                        title = 'Total Cost (USD)',
                        titlefont = dict(color=self.config.legend_font_color),
                    ),
                ),
                hovertemplate="<b>Total cost:</b> %{text} USD<br><b>ID:</b> %{customdata[0]}<br><b>Technology:</b> %{customdata[1]}<extra></extra>",
            )
        
        return l

    def tech_connection_layers(self):
        
        df = self.new_connected_schools.copy()

        layers = []

        for tech_ in df['technology'].unique():
            ff = df[df['technology'] == tech_]

            l = go.Scattermapbox(
                name = tech_ + ' connected',
                lat = ff['lat'],
                lon = ff['lon'],
                text = ff['total_cost'].map(lambda x: f'{x:,}'),
                customdata = ff['school_id'],
                mode = 'markers',
                marker = go.scattermapbox.Marker(
                    size = self.layer_config.tech_layer.marker_size,
                    color = self.layer_config.tech_layer.color_map[tech_],
                    opacity=self.layer_config.tech_layer.marker_opacity,
                ),
                hovertemplate="<b>ID:</b> %{customdata}<br><b>Total cost:</b> %{text} USD",
            )

            layers.append(l)
        
        return layers
    
    def fiber_node_layers(self):
        return [self.map_data_layers.fiber_layer_mb, self.map_data_layers.fiber_layer_mb_legend]
    
    def cell_tower_layers(self):
        return [self.map_data_layers.cell_tower_layer_mb, self.map_data_layers.cell_tower_layer_mb_legend]
    
    def infra_lines_layers(self):

        connections_ = dict(
            fiber = self.stats.fiber_connections,
            p2p = self.stats.p2p_connections,
        )

        layers = []
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
            
            l = go.Scattermapbox(
                name = tech_.capitalize() + ' lines',
                mode='lines',
                lat=lats,
                lon=lons,
                text = texts,
                line=dict(
                    width=self.layer_config.infra_lines_layer.line_width, 
                    color=self.layer_config.infra_lines_layer.line_color[tech_],
                ),
                showlegend = True,
                hoverinfo = 'none'
            )

            layers.append(l)

            if tech_ == 'fiber' and len(lats)>0:
                fs = self.fiber_schools
                ll = go.Scattermapbox(
                    name = 'Fiber school',
                    mode = 'markers',
                    lat = fs['lat'],
                    lon = fs['lon'],
                    customdata = fs['school_id'],
                    marker = go.scattermapbox.Marker(
                        color = '#8bd431',
                        size = 5,
                        opacity = .95
                    ),
                    hovertemplate="<b>ID:</b> %{customdata}",
                )
                layers.append(ll)
                layers = layers + self.fiber_node_layers()
            elif tech_ == 'p2p' and len(lats)>0:
                layers = layers + self.cell_tower_layers()
        
        layers = layers + self.tech_connection_layers()
        
        return layers
    

