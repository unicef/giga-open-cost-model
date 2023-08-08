from ipywidgets import (
    IntSlider,
    FloatSlider,
    Checkbox,
    Dropdown,
    Label,
    Layout,
    HBox,
    HTML,
)
from pydantic import BaseModel, root_validator
from IPython.display import display
from typing_extensions import Literal
from typing import Union, Dict, List
import numpy as np


class BaseParameter(BaseModel):

    show_default: bool = False

    def set_off_default_css_style(self, style_class: str):
        pass

    def update(self, value):
        pass


class IntSliderParameter(BaseParameter):

    """
    A model parameter that can be configured with an integer slider
    in a Jupyter notebook.
    """

    value: int
    min: int
    max: int
    step: int
    parameter_type: Literal["int_slider"]
    slider: IntSlider = None
    label: Label = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def parameter(self):
        if self.slider is None:
            self.slider = IntSlider(
                self.value, min=self.min, max=self.max, step=self.step
            )
        return self.slider

    @property
    def default_label(self):
        if self.label is None:
            self.label = Label(self.make_default_label(self.value))
        return self.label

    @property
    def parameter_with_default(self):
        return HBox([self.parameter, self.default_label])

    def make_default_label(self, value):
        return f"[default: {int(value)}]"

    def update(self, value: int):
        self.value = value
        self.parameter.value = value
        self.default_label.value = self.make_default_label(value)

    def set_off_default_css_style(self, style_class: str):
        def update_background(change):
            if self.value != self.slider.value:
                # change background color
                self.parameter.add_class(style_class)
                self.default_label.add_class(style_class)
            else:
                self.parameter.remove_class(style_class)
                self.default_label.remove_class(style_class)

        self.parameter.observe(update_background, names="value")

    def freeze(self):
        self.slider.disabled = True

    def unfreeze(self):
        self.slider.disabled = False


class FloatSliderParameter(BaseParameter):

    """
    A model parameter that can be configured with a float slider
    in a Jupyter notebook.
    """

    value: float
    min: float
    max: float
    step: float
    parameter_type: Literal["float_slider"]
    slider: FloatSlider = None
    label: Label = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def parameter(self):
        if self.slider is None:
            self.slider = FloatSlider(
                self.value, min=self.min, max=self.max, step=self.step
            )
        return self.slider

    @property
    def default_label(self):
        if self.label is None:
            self.label = Label(self.make_default_label(self.value))
        return self.label

    @property
    def parameter_with_default(self):
        return HBox([self.parameter, self.default_label])

    def make_default_label(self, value):
        return f"[default: {np.round(value, 2)}]"

    def update(self, value: float):
        self.value = value
        self.parameter.value = value
        self.default_label.value = self.make_default_label(value)

    def set_off_default_css_style(self, style_class: str):
        def update_background(change):
            if not np.isclose(self.value, self.slider.value, atol=self.step / 2):
                # change background color
                self.parameter.add_class(style_class)
                self.default_label.add_class(style_class)
            else:
                self.parameter.remove_class(style_class)
                self.default_label.remove_class(style_class)

        self.parameter.observe(update_background, names="value")

    def freeze(self):
        self.slider.disabled = True

    def unfreeze(self):
        self.slider.disabled = False


class BoolCheckboxParameter(BaseParameter):

    """
    A model parameter that can be configured with a boolean checkbox
    """

    value: bool
    description: str
    checkbox: Checkbox = None
    parameter_type: Literal["bool_checkbox"]

    class Config:
        arbitrary_types_allowed = True

    @property
    def parameter(self):
        if self.checkbox is None:
            self.checkbox = Checkbox(value=self.value, description=self.description)
        return self.checkbox

    def update(self, value: bool):
        self.value = value
        self.parameter.value = value

    def freeze(self):
        self.parameter.disabled = True

    def unfreeze(self):
        self.parameter.disabled = False


class CategoricalDropdownParameter(BaseParameter):

    """
    A model parameter that can be configured with a categorical dropdown widget.
    """

    options: List[str]
    value: str
    description: str
    dropdown: Dropdown = None
    parameter_type: Literal["categorical_dropdown"]
    layout: Dict = {"width": "400px"}

    class Config:
        arbitrary_types_allowed = True

    @property
    def parameter(self):
        if self.dropdown is None:
            self.dropdown = Dropdown(
                options=self.options,
                value=self.value,
                disabled=False,
                description=self.description,
                layout=Layout(**self.layout),
                style={"description_width": "initial"},
            )
        return self.dropdown

    def freeze(self):
        self.parameter.disabled = True

    def unfreeze(self):
        self.parameter.disabled = False


InputParameter = Union[
    IntSliderParameter,
    FloatSliderParameter,
    BoolCheckboxParameter,
    CategoricalDropdownParameter,
    CategoricalDropdownParameter,
]
