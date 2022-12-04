import math
from typing import List
from queue import PriorityQueue

from giga.schemas.geo import UniqueCoordinate, PairwiseDistance
from giga.models.nodes.graph.pairwise_distance_model import PairwiseDistanceModel
from giga.utils.progress_bar import managed_progress_bar


# helpers below can be pulled into a distance queue class in a future refactor
def add_distances(q, distances):
    for d in distances:
        priority, item = d.distance, d
        q.put((priority, item))
    return q


def move_item(source, target, identifier):
    item = source.pop(identifier)
    target[identifier] = item
    return item


class GreedyDistanceConnector:

    """
    Uses a greedy approach to iteratively connect the closest unconnected nodes to
    a subset of connected nodes.
    """

    def __init__(self, connected: List[UniqueCoordinate], **kwargs):
        self.connected = connected
        # used to compute distances between coordinate pairs
        self.distance_model = kwargs.get("distance_model", PairwiseDistanceModel())
        # if configured, allows connections that are less than the configured length
        self.maximum_connection_length_m = kwargs.get(
            "maximum_connection_length_m", math.inf
        )
        # if set to False only allows connections between the existing connected set
        # when set True, new dynamic connected coordinates can be used as connections
        self.dynamic_connect = kwargs.get("dynamic_connect", True)
        self.progress_bar = kwargs.get("progress_bar", False)

    def queue_pairwise_distances(self, q, set1, set2):
        distances = self.distance_model.run((set1, set2))
        distances = list(
            filter(lambda x: x.distance < self.maximum_connection_length_m, distances)
        )
        return add_distances(q, distances)

    def run(self, data: List[UniqueCoordinate], **kwargs) -> List[PairwiseDistance]:
        """
        Connects a list of unconnected unique coordinates in the input to
        a set of connected unique coordinates until no more connections are possible

        Inputs
        ----------
        data : List[UniqueCoordinate]
            A collection of UniqueCoordinates that contain a unique identifier
            and a location (usually lat/lon)

        Returns
        -------
        greedy_connected: List[PairwieDistance]
            A collection of ordered and connected coordinate pairs that have been
            added to the set of connected coordinates in this model.
            The pair wise distances in this collection are ordered based on
            when they were added to the connected set.
        """
        greedy_connected = []
        queue = (
            PriorityQueue()
        )  # priority queue is used to connect closest unconnected coordinates
        # create two look ups for connected (self.connected)
        # and unconnected (input data) coordinate sets
        connected_coordinates = {x.coordinate_id: x for x in self.connected}
        unconnected_coordinates = {x.coordinate_id: x for x in data}
        # add pairwise distances between all coordinates and in data to priority queue
        queue = self.queue_pairwise_distances(queue, data, self.connected)
        if self.progress_bar:
            pbar = managed_progress_bar(len(data))
        while not queue.empty():
            # iterate until priority queue is empty
            d, candidate = queue.get()  # fetch coordinate pair with closest distance
            id1, id2 = candidate.pair_ids
            connected1, connected2 = (
                id1 in connected_coordinates,
                id2 in connected_coordinates,
            )
            if connected1 and connected2:
                # if both items are connected skip, used to handle identical coordinates
                # not needed if coordinates in connected and unconnected sets are unique
                continue
            elif connected1 or connected2:
                # one item is not connected
                identifier = (
                    id2 if connected1 else id1
                )  # determine which coordinate needs to be connected
                # make new connection move from unconnected lookup to connected lookup
                new_connection = move_item(
                    unconnected_coordinates, connected_coordinates, identifier
                )
                greedy_connected.append(candidate)
                if self.progress_bar:
                    pbar.update(1)
                if self.dynamic_connect:
                    # if other unconnected coordinates can connect to new connection
                    queue = self.queue_pairwise_distances(
                        queue, list(unconnected_coordinates.values()), [new_connection]
                    )
            else:
                # neither items are connected, skip
                continue
        if self.progress_bar:
            pbar.update(pbar.total - pbar.n)
            pbar.close()
        return greedy_connected
