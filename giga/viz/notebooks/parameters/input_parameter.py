from ipywidgets import IntSlider, FloatSlider, Checkbox, Dropdown, Layout
from pydantic import BaseModel
from typing_extensions import Literal
from typing import Union, Dict, List


class IntSliderParameter(BaseModel):

    """
    A model parameter that can be configured with an integer slider
    in a Jupyter notebook.
    """

    value: int
    min: int
    max: int
    step: int
    parameter_type: Literal["int_slider"]

    @property
    def parameter(self):
        return IntSlider(self.value, min=self.min, max=self.max, step=self.step)


class FloatSliderParameter(BaseModel):

    """
    A model parameter that can be configured with a float slider
    in a Jupyter notebook.
    """

    value: float
    min: float
    max: float
    step: float
    parameter_type: Literal["float_slider"]

    @property
    def parameter(self):
        return FloatSlider(self.value, min=self.min, max=self.max, step=self.step)


class BoolCheckboxParameter(BaseModel):

    """
    A model parameter that can be configured with a boolean checkbox
    """

    value: bool
    description: str
    parameter_type: Literal["bool_checkbox"]

    @property
    def parameter(self):
        return Checkbox(value=self.value, description=self.description)


class CategoricalDropdownParameter(BaseModel):

    """
    A model parameter that can be configured with a categorical dropdown widget.
    """

    options: List[str]
    value: str
    description: str
    parameter_type: Literal["categorical_dropdown"]
    layout: Dict = {"width": "400px"}

    @property
    def parameter(self):
        return Dropdown(
            options=self.options,  # "Brazil"
            value=self.value,
            disabled=False,
            description=self.description,
            layout=Layout(**self.layout),
            style={"description_width": "initial"},
        )


InputParameter = Union[
    IntSliderParameter,
    FloatSliderParameter,
    BoolCheckboxParameter,
    CategoricalDropdownParameter,
    CategoricalDropdownParameter,
]
