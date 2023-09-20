import os
from pydantic import BaseModel
import plotly.graph_objs as go
import pandas as pd
from typing import List, Dict
import io
from ipywidgets import FileUpload, Label

from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.school import GigaSchoolTable
from giga.viz.notebooks.data_maps.map_data_layers import MapDataLayers, MapLayersConfig
from giga.viz.notebooks.components.widgets.giga_file_upload import GigaFileUpload
from giga.viz.notebooks.parameters.input_parameter import CategoricalDropdownParameter

MAP_BOX_ACCESS_TOKEN = os.environ.get("MAP_BOX_ACCESS_TOKEN", "")

SCHOOL_LAYERS_IDX_START = 2
SCHOOL_LAYERS_IDX_END = 6


class SelectionMapLayersConfig(MapLayersConfig):

    allow_connected_schools: bool = (
        True  # wether schools that are already connected can be selected
    )
    table_headers: List[str] = [
        "Project Connect Identifier",
        "School Name",
        "Connected",
        "Electricity",
        "Fiber",
    ]
    table_data_columns: List[str] = [
        "giga_id",
        "name",
        "connected",
        "has_electricity",
        "has_fiber",
    ]
    table_column_widths: List[float] = [2.5, 1.5, 1, 1, 1]
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
        if not self._schools.empty:
            self._schools["has_electricity"] = self._schools["has_electricity"].apply(
                lambda x: "Yes" if x else "No"
            )
        self._school_table_selector = None
        self._layers_selection = None
        self._layers_selection_no_cell = None
        self.selection_label = Label()

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
        layout = go.Layout()
        layout.paper_bgcolor = "#cde3e1"
        layout.width = 900
        layout.height = 550
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
                ],
                layout=layout,
            )
        return self._school_table_selector

    def connect_school_layer_selection(self, fig):
        def selection_fn(trace, points, selector):
            point_inds = list(points.point_inds)
            status = trace.name.strip()
            filtered_schools = self._schools[
                self._schools["connectivity_status"] == status
            ].reset_index()
            values = []
            if status == self.config.first_school_data_layer:
                # first trace in selection
                values = [
                    filtered_schools.loc[point_inds][col]
                    for i, col in enumerate(self.config.table_data_columns)
                ]
            else:
                for i, col in enumerate(self.config.table_data_columns):
                    vc = self.school_selection_table.data[0].cells.values[i] + list(
                        filtered_schools.loc[point_inds][col]
                    )
                    values.append(vc)
            self.school_selection_table.data[0].cells.values = values
            self.make_selected_label()

        for scatter in fig.data[SCHOOL_LAYERS_IDX_START:SCHOOL_LAYERS_IDX_END]:
            scatter.on_selection(selection_fn)

    @property
    def selected_schools(self):
        return self.school_selection_table.data[0].cells.values[0]


    def set_selected_schools(self, school_id_list):
        values = []
        schools = self._schools[self._schools['giga_id'].isin(school_id_list)]
        for i, col in enumerate(self.config.table_data_columns):
            values.append(list(
                schools[col]
            ))
        self.school_selection_table.data[0].cells.values = values
        self.make_selected_label()

    def make_selected_label(self):
        self.selection_label.value = (
            f"Total number of selected schools: {len(self.selected_schools)}"
        )
        return self.selection_label

    def make_upload_button(self, fig):
        def handle_upload(change):
            # Convert the uploaded file to a pandas DataFrame
            uploaded_file = change["new"][0]
            content = uploaded_file["content"]
            df = pd.read_csv(io.BytesIO(content))

            # Get the giga_school_id from the uploaded file
            uploaded_giga_school_id = df["school_id"].tolist()

            # Filter the _schools DataFrame to include only the uploaded giga_school_id
            filtered_schools = self._schools[
                self._schools["giga_id"].isin(uploaded_giga_school_id)
            ]
            self.school_selection_table.data[0].cells.values = [
                filtered_schools[col]
                for i, col in enumerate(self.config.table_data_columns)
            ]
            # Highlight the selected schools on the map
            for scatter in fig.data[
                SCHOOL_LAYERS_IDX_START:SCHOOL_LAYERS_IDX_END
            ]:
                scatter.selectedpoints = [
                    i
                    for i, giga_id in enumerate(scatter["customdata"])
                    if giga_id in uploaded_giga_school_id
                ]
            # Update the selection label
            self.selection_label.value = (
                f"Total number of selected schools: {len(self.selected_schools)}"
            )

        # Create an upload button that handles csv files - note that this will not handle files > 15MB
        upload_button = GigaFileUpload(
            accept=".csv",
            multiple=False,
            description="Upload Schools",
            button_color="#FAA95C",
        )
        upload_button.observe(handle_upload, "value")
        return upload_button
    
    def make_admin_dropdown(self,fig):
        def handle_select(change):
            if change['new']!='None' and change['new']!='---Admin 1---' and change['new']!='---Admin 2---':
                # Filter the _schools DataFrame to include only the uploaded giga_school_id
                filtered_schools = self._schools[(
                    (self._schools["admin1"].astype(str) == change["new"]) | (self._schools["admin2"].astype(str) == change["new"])
                )]
                self.school_selection_table.data[0].cells.values = [
                    filtered_schools[col]
                    for i, col in enumerate(self.config.table_data_columns)
                ]
                # Highlight the selected schools on the map
                for scatter in fig.data[
                    SCHOOL_LAYERS_IDX_START:SCHOOL_LAYERS_IDX_END
                ]:
                    scatter.selectedpoints = [
                        i
                        for i, giga_id in enumerate(scatter["customdata"])
                        if giga_id in list(filtered_schools['giga_id'])
                    ]
                # Update the selection label
                self.selection_label.value = (
                    f"Total number of selected schools: {len(self.selected_schools)}"
                )
            elif change['new']=='None':
                filtered_schools = self._schools
                self.school_selection_table.data[0].cells.values = [
                    filtered_schools[col]
                    for i, col in enumerate(self.config.table_data_columns)
                ]
                # Highlight the selected schools on the map
                for scatter in fig.data[
                    SCHOOL_LAYERS_IDX_START:SCHOOL_LAYERS_IDX_END
                ]:
                    scatter.selectedpoints = [
                        i
                        for i, giga_id in enumerate(scatter["customdata"])
                        #if giga_id in list(filtered_schools['giga_id'])
                    ]
                # Update the selection label
                self.selection_label.value = (
                    f"Total number of selected schools: {len(self.selected_schools)}"
                )

        options = ["None"]
        admins1 = list(set(obj.admin1 for obj in self.data_space.all_school_entities if obj.admin1!=''))
        if len(admins1)>0:
            options += ["---Admin 1---"] + admins1
        admins2 = list(set(obj.admin2 for obj in self.data_space.all_school_entities if obj.admin2!=''))
        if len(admins2)>0:    
            options += ["---Admin 2---"] + admins2
        admin_dropdown = CategoricalDropdownParameter(options=options,value="None",description="Dropdown to select admins", parameter_type = "categorical_dropdown").parameter
        admin_dropdown.observe(handle_select,"value")

        return admin_dropdown

    @property
    def layers_selection(self):
        if self._layers_selection is None:
            self._layers_selection = [
                self.fiber_layer_mb,
                self.cell_tower_layer_mb,
            ] + self.school_layers_mb
        return self._layers_selection

    @property
    def layers_selection_no_cell(self):
        if self._layers_selection is None:
            self._layers_selection = [
                self.fiber_layer_mb,
                self.cell_tower_layer_mb_empty,
            ] + self.school_layers_mb
        return self._layers_selection
