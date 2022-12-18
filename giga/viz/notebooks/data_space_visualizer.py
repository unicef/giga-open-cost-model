from giga.viz.notebooks.fiber import (
    plot_fiber_map,
    plot_data_map,
    plot_fiber_connections,
    default_rwanda_map,
    interactive_connection_history,
)
from giga.data.space.model_data_space import ModelDataSpace
from giga.schemas.output import CostResultSpace


class DataSpaceVisualizer:
    def __init__(self, data_space: ModelDataSpace):
        self.data_space = data_space

    def plot_data_map(self, **kwargs):
        school_coords = self.data_space.school_coordinates  # in blue
        fiber_coords = self.data_space.fiber_coordinates  # in green
        cell_tower_coords = self.data_space.cell_tower_coordinates
        return plot_data_map(
            fiber_coords, cell_tower_coords, school_coords, m=default_rwanda_map()
        )

    def plot_fiber_map(self, **kwargs):
        school_coords = self.data_space.school_coordinates  # in blue
        fiber_coords = self.data_space.fiber_coordinates  # in green
        return plot_fiber_map(fiber_coords, school_coords, m=default_rwanda_map())

    def plot_fiber_connections(self, results: CostResultSpace, **kwargs):
        school_coords = self.data_space.school_coordinates  # in blue
        fiber_coords = self.data_space.fiber_coordinates  # in green
        distances = results.technology_results.distances
        return plot_fiber_connections(
            fiber_coords, school_coords, distances, m=default_rwanda_map()
        )

    def interactive_fiber_connection_history(self, results, border, **kwargs):
        school_coords = self.data_space.school_coordinates  # in blue
        fiber_coords = self.data_space.fiber_coordinates  # in green
        distances = results.technology_results.distances
        return interactive_connection_history(
            border, fiber_coords, school_coords, distances
        )
