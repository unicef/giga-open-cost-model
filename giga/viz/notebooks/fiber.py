from ipywidgets import interactive
import matplotlib.pyplot as plt
import folium
import numpy as np


METERS_IN_KM = 1000.0

"""
   Map Plots
"""


def default_map(tiles="cartodbpositron", zoom_start=8, location=[-1.9, 30.1]):
    return folium.Map(location=location, tiles=tiles, zoom_start=zoom_start)


def default_rwanda_map(tiles="cartodbpositron", zoom_start=8, location=[-1.9, 30.1]):
    return folium.Map(location=location, tiles=tiles, zoom_start=zoom_start)


def default_brazil_map(
    tiles="cartodbpositron", zoom_start=4, location=[-17.39, -46.32]
):
    return folium.Map(location=location, tiles=tiles, zoom_start=zoom_start)


def plot_coordinate_map(
    coordinates,
    coordinate_name="Coordinate",
    show_id=True,
    show_properties=False,
    color="green",
    coordinate_radius=2,
    m=folium.Map(tiles="cartodbpositron", zoom_start=10),
):
    for c in coordinates:
        popup = f"{coordinate_name}"
        if show_id:
            popup += f" {c.coordinate_id}"
        if show_properties:
            for k, v in c.properties.items():
                popup += f" {k}: {v}"
        folium.CircleMarker(
            location=c.coordinate,
            popup=popup,
            color=color,
            fill=True,
            radius=coordinate_radius,
        ).add_to(m)
    return m


def plot_pairwise_connections(
    connections, color="gold", weight=2, opacity=0.8, m=default_rwanda_map()
):
    total_dist_km = sum(list(map(lambda x: x.distance, connections))) / METERS_IN_KM
    title_html = """
             <h3 align="center" style="font-size:16px"><b>{}</b></h3>
             """.format(
        f"Total length of connections: {np.round(total_dist_km, 2)} km"
    )

    for c in connections:
        popup = f"distance: {np.round(c.distance / METERS_IN_KM, decimals=2)} km"
        loc = [c.coordinate1.coordinate, c.coordinate2.coordinate]
        folium.PolyLine(
            loc, color=color, weight=weight, opacity=opacity, popup=popup
        ).add_to(m)
    m.get_root().html.add_child(folium.Element(title_html))
    return m


def plot_fiber_map(fiber_coordinates, school_coordinates, m=default_rwanda_map()):
    m = plot_coordinate_map(
        school_coordinates,
        coordinate_name="School",
        show_id=False,
        show_properties=True,
        color="#43adde",
        m=m,
    )
    m = plot_coordinate_map(
        fiber_coordinates,
        coordinate_name="Fiber Node",
        color="black",
        coordinate_radius=3,
        m=m,
    )
    return m


def plot_data_map(
    fiber_coordinates,
    cell_tower_coordinates,
    school_coordinates,
    m=default_rwanda_map(),
    **kwargs,
):
    m = plot_coordinate_map(
        fiber_coordinates, coordinate_name="Fiber Node", color="#68e389", m=m, **kwargs
    )
    m = plot_coordinate_map(
        cell_tower_coordinates,
        coordinate_name="Cell Tower",
        color="#bfb673",
        m=m,
        **kwargs,
    )
    m = plot_coordinate_map(
        school_coordinates,
        coordinate_name="School",
        show_id=False,
        show_properties=True,
        color="#43adde",
        m=m,
        **kwargs,
    )
    return m


def plot_fiber_connections(
    fiber_coordinates, school_coordinates, connections, m=default_rwanda_map(),
    title="Current Fiber Connections"
):
    m = plot_coordinate_map(
        school_coordinates,
        coordinate_name="School",
        show_id=True,
        show_properties=True,
        color="#43adde",
        m=m,
    )
    m = plot_pairwise_connections(connections, color="#dbcb3b", m=m)
    m = plot_coordinate_map(
        fiber_coordinates,
        coordinate_name="Fiber Node",
        color="black",
        coordinate_radius=3,
        m=m,
    )

    title_html = f"""
        <h3 align="center" style="font-size:18px"><b>{title}</b></h3>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    return m


"""
   Interactive Plots
"""


def plot_static_connections(border, fiber, schools, connections):
    # initialize an axis
    fig, ax = plt.subplots(figsize=(8, 6))
    # plot border on axis
    border.plot(color="lightgrey", ax=ax)
    # plot fiber
    lat, lng = list(map(lambda x: x.coordinate[0], fiber)), list(
        map(lambda x: x.coordinate[1], fiber)
    )
    plt.plot(lng, lat, "go")
    # plot schools
    lat, lng = list(map(lambda x: x.coordinate[0], schools)), list(
        map(lambda x: x.coordinate[1], schools)
    )
    plt.plot(lng, lat, "bo")
    # plot connections
    for d in connections:
        lat = [d.coordinate1.coordinate[0], d.coordinate2.coordinate[0]]
        lng = [d.coordinate1.coordinate[1], d.coordinate2.coordinate[1]]
        plt.plot(lng, lat, color="#dbcb3b")

    # add grid
    ax.grid(b=True, alpha=0.5)
    plt.show()


def interactive_connection_history(border, fiber, schools, connections):
    iterations = len(connections)

    def render(iteration):
        plot_static_connections(border, fiber, schools, connections[0:iteration])

    interactive_plot = interactive(render, iteration=(0, iterations))
    return interactive_plot
