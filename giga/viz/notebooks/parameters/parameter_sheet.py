import ipywidgets as widgets
from IPython.display import display
from typing import Dict, List
from pydantic import parse_obj_as

from giga.viz.notebooks.parameters.input_parameter import InputParameter


CELL_STYLE_UPDATED_DEFAULT = """
.off-default-cell-background-color {
    background-color: rgba(242, 228, 102, 0.65);
    margin: 0px;
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

    def __init__(self, sheet_name, parameters: List[Dict], columns=2, width="1000px"):
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

    def _create_sheet(self):
        # Calculate the number of rows needed
        rows = len(self.parameters)

        # Create a GridspecLayout with the calculated number of rows and columns
        grid = widgets.GridspecLayout(rows, self.columns, width=self.width)

        # Add parameter labels and interactive widgets to the grid
        for i, p in enumerate(self.parameters):
            row = i
            grid[row, 0] = widgets.HTML(value=p["parameter_input_name"])
            if self.interactive_parameters[i].show_default:
                grid[row, 1] = self.interactive_parameters[i].parameter_with_default
            else:
                grid[row, 1] = self.interactive_parameters[i].parameter
            self._sheet_lookup[p["parameter_name"]] = self.interactive_parameters[
                i
            ].parameter
            # add a callback to update the background color of the cell
            self.interactive_parameters[i].set_off_default_css_style(
                "off-default-cell-background-color"
            )
        return grid

    def input_parameters(self):
        """
        Returns a Jupyter widget that allows user input into the parameter sheet
        """
        if self.sheet is None:
            self.sheet = self._create_sheet()
            return self.sheet
        else:
            return self.sheet
