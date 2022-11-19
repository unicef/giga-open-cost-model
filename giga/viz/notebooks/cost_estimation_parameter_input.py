import math
import io
from ipywidgets import FloatSlider, IntSlider, Checkbox, Dropdown, FileUpload, VBox, Layout
from ipysheet import sheet, column, row, cell, to_dataframe

import pandas as pd

from giga.schemas.conf.models import FiberTechnologyCostConf
from giga.schemas.conf.data import DataSpaceConf
from giga.schemas.geo import UniqueCoordinateTable


FIBER_MODEL_PARAMETERS = [{'parameter_name': 'cost_per_km', 'parameter_input_name': 'Cost Per km (USD)', 'parameter_interactive': IntSlider(7_500, min=0, max=50_000, step=100)},
                          {'parameter_name': 'fixed_costs', 'parameter_input_name': 'Maintanance Cost (USD)', 'parameter_interactive': IntSlider(0, min=0, max=5_000, step=10)},
                          {'parameter_name': 'maximum_connection_length', 'parameter_input_name': 'Maximum Connection Length (km)', 'parameter_interactive': IntSlider(250, min=0, max=500)},
                          {'parameter_name': 'economies_of_scale', 'parameter_input_name': 'Economies of Scale', 'parameter_interactive': Checkbox(value=True, description='ON')}]

DATA_SPACE_PARAMETERS = [{'parameter_name': 'country_name', 'parameter_input_name': 'Country', 'parameter_interactive': Dropdown(options=['Sample', 'Brazil', 'Rwanda'], value='Brazil', description='Country:', layout=Layout(width='400px'))},
                         {'parameter_name': 'fiber_map_upload', 'parameter_input_name': 'Fiber Map', 'parameter_interactive': FileUpload(accept='.csv', multiple=False, description='Upload Fiber Map', layout=Layout(width='400px'))}]

            

class CostEstimationParameterInput:
    
    def __init__(self):
        self._hashed_sheets = {}

    def fiber_parameters_input(self, sheet_name='fiber'):
        s = sheet(sheet_name, columns=2, rows=len(FIBER_MODEL_PARAMETERS), column_headers=False, row_headers=False, column_width=2)
        name_column = column(0, list(map(lambda x: x['parameter_input_name'], FIBER_MODEL_PARAMETERS)))
        input_column = column(1, list(map(lambda x: x['parameter_interactive'], FIBER_MODEL_PARAMETERS)))
        return s
    
    def fiber_parameters(self, sheet_name='fiber'):
        s = sheet(sheet_name)
        df = to_dataframe(s)
        cost_per_km = float(df[df['A'] == 'Cost Per km (USD)']['B'])
        economies_of_scale = bool(float(df[df['A'] == 'Economies of Scale']['B']))
        fixed_costs = float(df[df['A'] == 'Maintanance Cost (USD)']['B'])
        maximum_connection_length = float(df[df['A'] == 'Maximum Connection Length (km)']['B']) * 1000.0 # meters
        return FiberTechnologyCostConf(capex={'cost_per_km': cost_per_km, 'economies_of_scale': economies_of_scale},
                                       opex={'fixed_costs': fixed_costs},
                                       constraints={'maximum_connection_length': maximum_connection_length})
    
    def data_parameters_input(self, sheet_name='data'):
        self._hashed_sheets[sheet_name] = {p['parameter_name']: p['parameter_interactive'] for p in DATA_SPACE_PARAMETERS}
        return VBox(list(map(lambda x: x['parameter_interactive'], DATA_SPACE_PARAMETERS)))
    
    def data_parameters(self, sheet_name='data', local_workspace=None):
        s = self._hashed_sheets[sheet_name]
        country_id = s['country_name'].value
        up = s['fiber_map_upload'].value[0].content
        content = UniqueCoordinateTable.from_csv(io.BytesIO(up))
        return DataSpaceConf(school_data_conf={'country_id': country_id, 'transport': {'workspace': local_workspace}}, fiber_map_conf={'map_type': 'fiber-nodes', 'coordinate_map': content})
    
    def parameter_input(self):
        f = self.fiber_parameters_input()
        d = self.data_parameters_input()
        return VBox([f, d])
