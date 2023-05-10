from ipywidgets import FileUpload, ButtonStyle


class GigaFileUpload(FileUpload):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.style = ButtonStyle(
            button_color="#ffe3c9",  # yellow background
            border_radius="20px",  # rounded corners
        )
