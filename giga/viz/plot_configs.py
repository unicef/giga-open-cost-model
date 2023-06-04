# configuration for maps without selection
STATIC_MAP_MODEBAR_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d",
        "pan2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "toggleSpikelines",
        "select",
        "lasso",
    ],
    "toImageButtonOptions": {
        "format": "jpeg",  # one of png, svg, jpeg, webp
        "filename": "custom_image",
        "height": 1600,
        "width": 1600,
    },
    "displaylogo": False,
}

# configuration for selection maps is done over two config dicts
SELECTION_MAP_MODEBAR_BUTTON_CONFIG = {
    "activecolor": "#FFFFFF",
    "remove": [
        "zoom2d",
        "zoomin",
        "zoomout",
        "autoScale2d",
        "resetScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "toggleSpikelines",
    ],
}

SELECTION_MAP_MODEBAR_GLOBAL_CONFIG = {
    "toImageButtonOptions": {
        "format": "jpeg",  # one of png, svg, jpeg, webp
        "filename": "custom_image",
        "height": 1600,
        "width": 1600,
    },
    "displaylogo": False,
    "displayModeBar": True,
}
