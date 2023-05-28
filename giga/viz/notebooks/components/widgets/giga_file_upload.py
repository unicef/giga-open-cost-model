from ipywidgets import FileUpload, ButtonStyle


class GigaFileUpload(FileUpload):
    def __init__(self, *args, **kwargs):
        button_color = kwargs.pop("button_color", "#ffe3c9")  # default black
        super().__init__(*args, **kwargs)

        # Estimate button width
        estimated_width = len(self.description) * 1.0

        self.style = ButtonStyle(
            button_color=button_color,  # yellow background
            border_radius="20px",  # rounded corners
        )

        # Set estimated width
        self.layout.width = f"{estimated_width}em"
