import ipysheet
from pydantic import parse_obj_as

from giga.viz.notebooks.parameters.input_parameter import InputParameter


class ParameterSheet:
    """
    Helper class to create and manage parameter sheets.
    Allows defaults to be set for each parameter, and
    allow custom values to be set for each parameter through
    a Jupyter widget input.
    """

    def __init__(self, sheet_name, parameters, columns=2, column_width=2):
        """
        sheet_name: Name of the sheet
        parameters: dictionary of parameters containing
            parameter name, dispaly name, interactive widget, and scaling factor
        """
        self.sheet_name = sheet_name
        self.columns = columns
        self.column_width = column_width
        self.parameters = parameters
        self.interactive_parameters = [
            parse_obj_as(InputParameter, p["parameter_interactive"]).parameter
            for p in self.parameters
        ]
        self.sheet = None

    def update_parameter(self, name, value):
        """
        Updates the value of a parameter
        """
        for i, p in enumerate(self.parameters):
            if p["parameter_name"] == name:
                self.interactive_parameters[i].value = value
                break

    def _create_sheet(self):
        # unpack parameters and refence them
        sheet = ipysheet.sheet(
            self.sheet_name,
            columns=self.columns,
            rows=len(self.parameters),
            column_headers=False,
            row_headers=False,
            column_width=self.column_width,
        )
        name_column = ipysheet.column(
            0,
            list(map(lambda x: x["parameter_input_name"], self.parameters)),
        )
        input_column = ipysheet.column(1, self.interactive_parameters)
        return sheet

    def input_parameters(self):
        """
        Returns a jupyter widget that allows user input into the parameter sheet
        """
        if self.sheet is None:
            self.sheet = self._create_sheet()
            return self.sheet
        else:
            return self.sheet
