from collections import OrderedDict


ORDERED_COST_COLORS = ["#d8e4e8", "#AFD3E2", "#19A7CE", "#146C94"]

# for cumulative distance distribution bar plots
ORDERED_CUMULATIVE_DISTANCE_COLORS = [
    "#009dff",
    "#59bfff",
    "#8cd3ff",
    "#bfe6ff",
    "#e8ffff",
]

COST_COLORS_TRIPLET = ["#AFD3E2", "#19A7CE", "#146C94"]

COST_COLORS_PAIR = ["#AFD3E2", "#146C94"]

# for technology maps
GIGA_TECHNOLOGY_COLORS = {
    "Cellular": "#46c66d",
    "Satellite": "#f94b4b",
    "P2P": "#ff9f40",
    "Fiber": "#277aff",
}

# for primary maps that include school connectivity status
GIGA_CONNECTIVITY_COLORS = {
    "Good": "#8bd431",
    "Moderate": "#ffc93d",
    "No connection": "#ff615b",
    "Unknown": "#DF9997",  # Project connect color is: "#556fc2"
}

# for cellular coverage map
CELL_COVERAGE_COLOR_MAP = OrderedDict({
        "None": "#e8ffff",
        "2G": "#bfe6ff",
        "3G": "#8cd3ff",
        "4G": "#009dff",
        "LTE": "#009dff", # same as 4G
    })

# for satellite breakdown pie chart
SATELLITE_BREAKDOWN_COLORS = {"Satellite": "#f94b4b", "Other": "#277aff"}

# for fiber distance infrastructure maps
FIBER_COLORBAR_MIN = 0
FIBER_COLORBAR_MAX = 20

# for cell tower distance infrastructure maps
CELLULAR_COLORBAR_MIN = 0
CELLULAR_COLORBAR_MAX = 10

# colors used in titles and other styling options
GIGA_BLACK = "#222222"
GIGA_WHITE = "#ffffff"
