import ipywidgets as widgets
from pydantic import BaseModel

from giga.data.stats.result_stats import ProjectOverview


def format_integer_with_commas(number):
    return "{:,}".format(round(number)).replace(",", ",\u200A")


def project_overview_entry(title, subtitle):
    layout = widgets.Layout(
        display="flex",
        justify_content="center",
        align_items="center",
        width="100%",
        height="200px",
    )

    title_widget = widgets.HTML(
        value=f"<center><font face='Calibri' color='black'><h1>{title}</h1></font></center>"
    )

    subtitle_widget = widgets.HTML(
        value=f"<center><font face='Calibri' color='black' style='font-size:20px;'>{subtitle}</font></center>"
    )

    return widgets.VBox([title_widget, subtitle_widget], layout=layout)


def project_overview_grid(overview: ProjectOverview):
    # create overview layout
    widget1 = project_overview_entry(
        format_integer_with_commas(overview.schools_connected_project),
        f"Schools Connected in Project for a Total of {format_integer_with_commas(overview.schools_connected_project + overview.schools_connected_current)}",
    )
    widget2 = project_overview_entry(
        format_integer_with_commas(overview.students_connected_project),
        "Children Connected in Project",
    )
    widget3 = project_overview_entry(
        f"{format_integer_with_commas(overview.connected_percentage_projected)}%",
        f"Schools Connected in the country from base of {format_integer_with_commas(overview.connected_percentage_current)}%",
    )
    widget4 = project_overview_entry(
        f"{format_integer_with_commas(overview.average_mbps)} Mbps",
        "Average Mbps Delivered",
    )
    widget5 = project_overview_entry(
        format_integer_with_commas(overview.schools_without_electricity),
        f"Schools without Electricity, or {overview.schools_without_electricity_percentage}%",
    )
    widget6 = project_overview_entry(
        format_integer_with_commas(overview.schools_with_electricity),
        f"Schools with Electricity, or {overview.schools_with_electricity_percentage}%",
    )
    grid = widgets.GridBox(
        [widget1, widget2, widget3, widget4, widget5, widget6],
        layout=widgets.Layout(grid_template_columns="repeat(2, 1fr)"),
    )
    return grid
