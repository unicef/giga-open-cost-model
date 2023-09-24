import ipywidgets as widgets
from IPython.display import display
from typing import Dict, List
from pydantic import parse_obj_as

from giga.viz.notebooks.parameters.input_parameter import InputParameter

LABELS = ["<b>Capex:</b>","<b>Opex:</b>","<b>Constraints:</b>","<b>Options:</b>"]

CELL_STYLE_UPDATED_DEFAULT = """
.off-default-cell-background-color {
    background-color: rgba(255, 227, 201, 0.95);
    margin: 0px;
}

.param-text-box {
    margin-bottom: -5px;
    margin-top: 5px;
}


"""

display(widgets.HTML(f"<style>{CELL_STYLE_UPDATED_DEFAULT}</style>"))


class ParameterSheet:
    """
    Helper class to create and manage parameter sheets.
    Allows defaults to be set for each parameter, and
    allow custom values to be set for each parameter through
    a Jupyter widget input.
    """

    def __init__(self, sheet_name, parameters: List[Dict], label_pos = [], columns=2, width="1000px"):
        """
        sheet_name: Name of the sheet
        parameters: list of dictionaries containing
            parameter name, display name, and interactive widget
        columns: number of columns in the grid layout
        """
        self.sheet_name = sheet_name
        self.columns = columns
        self.width = width
        self.parameters = parameters
        self.label_pos = label_pos
        self.interactive_parameters = [
            parse_obj_as(InputParameter, p["parameter_interactive"])
            for p in self.parameters
        ]
        self.sheet = None
        self._sheet_lookup = {}

    def update_parameter(self, name, value):
        """
        Updates the value of a parameter
        """
        for i, p in enumerate(self.parameters):
            if p["parameter_name"] == name:
                self.interactive_parameters[i].update(value)
                break

    def get_interactive_parameter(self, name):
        """
        Returns the value of a parameter
        """
        for i, p in enumerate(self.parameters):
            if p["parameter_name"] == name:
                return self.interactive_parameters[i].parameter
        return None

    def get_parameter_value(self, parameter_name):
        if self.sheet is None:
            self.sheet = self._create_sheet()
        return self._sheet_lookup[parameter_name].value

    def _create_sheet(self, show_defaults = True):
        # Calculate the number of rows needed
        rows = len(self.parameters)

        def _create_row(i, p):
            if self.interactive_parameters[i].show_default and show_defaults:
                param = self.interactive_parameters[i].parameter_with_default
                # add a callback to update the background color of the cell
                self.interactive_parameters[i].set_off_default_css_style(
                    "off-default-cell-background-color"
                )
            else:
                param = self.interactive_parameters[i].parameter
            self._sheet_lookup[p["parameter_name"]] = self.interactive_parameters[
                i
            ].parameter
            return widgets.VBox(
                [
                    widgets.HTML(value=p["parameter_input_name"]).add_class(
                        "param-text-box"
                    ),
                    param,
                ]
            ).add_class("param-row")
        
        params = [_create_row(i, p) for i, p in enumerate(self.parameters)]
        if len(self.label_pos)==0:
            return widgets.VBox(params)
        
        for i in range(len(self.label_pos)):
            params.insert(self.label_pos[i]+i,widgets.HTML(value=LABELS[i]))
        return widgets.VBox(params)

    def input_parameters(self, show_defaults = True):
        """
        Returns a Jupyter widget that allows user input into the parameter sheet
        """
        if self.sheet is None:
            self.sheet = self._create_sheet(show_defaults)
            return self.sheet
        else:
            return self.sheet

    def freeze(self):
        for p in self.interactive_parameters:
            p.freeze()

    def unfreeze(self):
        for p in self.interactive_parameters:
            p.unfreeze()
