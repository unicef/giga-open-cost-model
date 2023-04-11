import math
from typing import List
from queue import PriorityQueue
import numpy as np

from giga.schemas.geo import UniqueCoordinate, PairwiseDistance
from giga.models.nodes.graph.pairwise_distance_model import PairwiseDistanceModel
from giga.utils.progress_bar import managed_progress_bar
from giga.schemas.distance_cache import GreedyConnectCache


EPS = 1e-5  # for tie-breakers in queue with equal distances


# helpers below can be pulled into a distance queue class in a future refactor
def add_distances(q, distances):
    for d in distances:
        priority, item = d.distance + np.random.uniform(0.0, EPS), d
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

    def __init__(
        self,
        connected: List[UniqueCoordinate],
        distance_cache: GreedyConnectCache = None,
        **kwargs
    ):
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
        self._cache = (
            distance_cache if distance_cache is not None else GreedyConnectCache()
        )

    def _queue_non_cached(self, q, set1, set2):
        distances = self.distance_model.run((set1, set2))
        distances = list(
            filter(lambda x: x is not None and x.distance < self.maximum_connection_length_m, distances)
        )
        return add_distances(q, distances)

    def _queue_from_cache(self, q, set1, set2, cache):
        if cache.cache_type == "one-to-one":
            coord_ids = [c.coordinate_id for c in set1]
            distances = [cache.lookup.get(cid, None) for cid in coord_ids]
        elif cache.cache_type == "one-to-many":
            # single cache in set 2
            coord_ids = [c.coordinate_id for c in set2]
            distances = []
            for cid in coord_ids:
                distances += cache.lookup[cid]
        else:
            raise Exception("Trying to use a cache of unsupported type")
        distances = list(
            filter(lambda x: x is not None and x.distance < self.maximum_connection_length_m, distances)
        )
        return add_distances(q, distances)

    def queue_pairwise_distances(self, q, set1, set2, cache=None):
        if cache:
            return self._queue_from_cache(q, set1, set2, cache)
        else:
            return self._queue_non_cached(q, set1, set2)

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
        # create a source tracker
        sources = {x.coordinate_id: x.coordinate_id for x in self.connected}
        # add pairwise distances between all coordinates and in data to priority queue
        queue = self.queue_pairwise_distances(
            queue, data, self.connected, cache=self._cache.connected_cache
        )
        if self.progress_bar:
            pbar = managed_progress_bar(len(data), description="Distance Connect Model")
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
            elif connected2:
                # coordinate 1 is not connected
                # make new connection move from unconnected lookup to connected lookup
                new_connection = move_item(
                    unconnected_coordinates, connected_coordinates, id1
                )
                # fetch for source use id2 if doesn't exist
                candidate.coordinate1.properties["source"] = sources[id2]
                sources[id1] = sources[id2]
                greedy_connected.append(candidate)
                if self.progress_bar:
                    pbar.update(1)
                if self.dynamic_connect:
                    # if other unconnected coordinates can connect to new connection
                    queue = self.queue_pairwise_distances(
                        queue,
                        list(unconnected_coordinates.values()),
                        [new_connection],
                        cache=self._cache.unconnected_cache,
                    )
            else:
                # neither items are connected, skip
                continue
        if self.progress_bar:
            pbar.update(pbar.total - pbar.n)
            pbar.close()
        return greedy_connected
