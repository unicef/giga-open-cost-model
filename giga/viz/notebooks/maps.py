from ipywidgets import interactive
import matplotlib.pyplot as plt
import folium
from folium.plugins import Draw
import numpy as np
import branca.colormap as cm

from giga.viz.notebooks.helpers import output_to_table


def show_electricity_map(data_space):

    m = folium.Map(tiles="cartodbpositron", zoom_start=8, location=[-1.9, 30.1])

    for s in data_space.school_entities:
        popup = f"School ID: {s.giga_id}"
        if s.has_electricity:
            color = "#ffd74d"
        else:
            color = "black"
        folium.CircleMarker(
            location=[s.lat, s.lon],
            popup=popup,
            color=color,
            fill=True,
            radius=2,
        ).add_to(m)
    for c in data_space.cell_tower_coordinates:
        popup = f"{c.coordinate_id}"
        folium.CircleMarker(
            location=c.coordinate,
            popup=popup,
            color="#bab8b1",
            fill=True,
            radius=1,
        ).add_to(m)
    for c in data_space.fiber_coordinates:
        popup = f"{c.coordinate_id}"
        folium.CircleMarker(
            location=c.coordinate,
            popup=popup,
            color="#bab8b1",
            fill=True,
            radius=1,
        ).add_to(m)

    return m


def show_cost_map(data_space, output_space):
    table = output_to_table(output_space)
    table = table[table["total_cost"].notna()]
    cost_lookup = {
        str(row["school_id"]): float(row["total_cost"]) for i, row in table.iterrows()
    }

    m = folium.Map(tiles="cartodbpositron", zoom_start=8, location=[-1.9, 30.1])
    linear = cm.LinearColormap(
        ["green", "yellow", "red"],
        vmin=table["total_cost"].min(),
        vmax=table["total_cost"].max(),
    )

    for s in data_space.school_entities:
        popup = f"School ID: {s.giga_id}"
        if s.giga_id in cost_lookup:
            popup += f"\nCost: ${int(cost_lookup[s.giga_id])}.00"
            color = linear(cost_lookup[s.giga_id])
        else:
            color = "#fff1c2"
        folium.CircleMarker(
            location=[s.lat, s.lon],
            popup=popup,
            color=color,
            fill=True,
            radius=2,
        ).add_to(m)
    for c in data_space.cell_tower_coordinates:
        popup = f"{c.coordinate_id}"
        folium.CircleMarker(
            location=c.coordinate,
            popup=popup,
            color="#bab8b1",
            fill=True,
            radius=1,
        ).add_to(m)
    for c in data_space.fiber_coordinates:
        popup = f"{c.coordinate_id}"
        folium.CircleMarker(
            location=c.coordinate,
            popup=popup,
            color="black",
            fill=True,
            radius=1,
        ).add_to(m)

    return m
