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


def make_run_button(callback):
    return make_button(
        callback, "Run Model", button_color="#f5f5f5", height="40px", width="300px"
    )


def make_run_again_button(callback):
    return make_button(callback, "Run Model Again", button_color="#d6e4fd")


def create_event_button(callback, title="Click Me"):
    # Create the button
    button = Button(
        description=title,
        layout=Layout(width="216px"),
        # button_style='info', # This gives the button a blue color
        style={"button_color": "#d6e4fd", "font_size": "12px"},
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
