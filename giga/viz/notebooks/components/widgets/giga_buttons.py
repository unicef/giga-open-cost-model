from ipywidgets import Button, ButtonStyle, Layout

from ipywidgets import Button, ButtonStyle, Layout
from IPython.display import HTML, display


display(HTML("<style>.widget-button { border-radius: 6px !important; }</style>"))


class CustomButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_on_click_event(self, callback):
        self.on_click(callback)

    def set_style(self, **kwargs):
        self.style = ButtonStyle(**kwargs)

    def set_layout(self, **kwargs):
        self.layout = Layout(**kwargs)


def make_button(callback, description, **kwargs):
    button = CustomButton(description=description)
    button.set_style(**kwargs)
    button.set_layout(**kwargs)
    button.add_on_click_event(callback)
    return button


def make_rounded_button(callback, description, **kwargs):
    return make_button(
        callback,
        description,
        height="40px",
        width="200px",
        border_radius="2px",
        margin="6px",
        box_shadow="1px 1px 3px #ccc",
        **kwargs
    )


def make_run_button(callback):
    return make_rounded_button(
        callback, "Run Model", button_color="#ffe3c9", border="1px solid #ff9f40"
    )


def make_run_again_button(callback):
    return make_rounded_button(
        callback, "Run Model Again", button_color="#ffe3c9", border="1px solid #ff9f40"
    )


def make_show_maps_button(callback):
    return make_rounded_button(
        callback, "Show All Maps", button_color="#ffe3c9", border="1px solid #ff9f40"
    )


def make_show_full_table_button(callback):
    return make_rounded_button(
        callback, "Show Full Table", button_color="#ffe3c9", border="1px solid #ff9f40"
    )


def create_event_button(callback, title="Click Me"):
    button = make_rounded_button(
        callback, title, button_color="#ffe3c9", border="1px solid #ff9f40"
    )
    # Set the border-radius to make the button edges rounded
    button.add_class("widget-button")
    # Assign the callback function to the button's 'on_click' event
    button.on_click(callback)
    return button


def make_run_again_button(inputs, result_output, run_model_button):
    def update_to_runnable(event):
        inputs.unfreeze()
        result_output.clear_output()
        run_model_button.disabled = False

    return create_event_button(update_to_runnable, title="Run Model Again")
