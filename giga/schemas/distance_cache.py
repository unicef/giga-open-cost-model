import os
from pydantic import BaseModel
from typing import List, Dict
import pandas as pd

try:
    import ujson as json
except ImportError:
    import json

from giga.schemas.geo import PairwiseDistance, UniqueCoordinate


def encode_coord(coord):
    # turn tuple to list
    coord["coordinate"] = list(coord["coordinate"])
    return json.dumps(coord)


def decode_coord(coord):
    return UniqueCoordinate(**json.loads(coord))


class SingleLookupDistanceCache(BaseModel):
    """Cache for existing distance data with one to one mapping"""

    lookup: Dict[str, PairwiseDistance]
    cache_type: str = "one-to-one"

    @staticmethod
    def from_distances(distances):
        # turn a List[PairwieDistance] into Dict[id, PairwiseDistance]
        tmp = {}
        for p in distances:
            id_source, id_target = p.pair_ids
            if id_source == id_target:
                continue
            else:
                if id_source in tmp:
                    tmp[id_source].append((id_target, p))
                else:
                    tmp[id_source] = [(id_target, p)]
        # source -> closest
        lookup = {}
        for k, v in tmp.items():
            closest_id, closest_distance = min(v, key=lambda x: x[1].distance)
            lookup[k] = closest_distance
        return SingleLookupDistanceCache(lookup=lookup)

    @staticmethod
    def from_json(file):
        with open(file, "r") as f:
            d = json.load(f)
        return SingleLookupDistanceCache(**d)

    def to_json(self, file):
        with open(file, "w") as f:
            json.dump(self.dict(), f)

    @staticmethod
    def from_csv(file):
        table = pd.read_csv(file)
        lookup = {}
        for i, row in table.iterrows():
            pair_ids = tuple(row.pair_ids.split(","))
            source_id = pair_ids[0]
            lookup[source_id] = PairwiseDistance(
                pair_ids=pair_ids,
                distance=row.distance,
                coordinate1=decode_coord(row.coordinate1),
                coordinate2=decode_coord(row.coordinate2),
                distance_type=row.distance_type,
            )
        return SingleLookupDistanceCache(lookup=lookup)

    def to_csv(self, file):
        flat = [v.dict() for v in self.lookup.values()]
        for c in flat:
            c["coordinate1"] = encode_coord(c["coordinate1"])
            c["coordinate2"] = encode_coord(c["coordinate2"])
            c["pair_ids"] = ",".join(c["pair_ids"])
        pd.DataFrame(flat).to_csv(file, index=False)

    def __len__(self):
        return len(self.lookup)


class MultiLookupDistanceCache(BaseModel):
    """Cache for existing distance data with one to many mapping"""

    lookup: Dict[str, List[PairwiseDistance]]
    n_neighbors: int
    cache_type: str = "one-to-many"

    @staticmethod
    def from_distances(distances, n_neighbors=10):
        tmp = {}
        for p in distances:
            id_source, id_target = p.pair_ids
            if id_source == id_target:
                continue
            else:
                # reverse ID ordering to preserve edge direction
                revids = p.copy()
                revids.pair_ids = tuple(reversed(revids.pair_ids))
                revids.coordinate1, revids.coordinate2 = (
                    revids.coordinate2,
                    revids.coordinate1,
                )
                if id_source in tmp:
                    tmp[id_source].append(revids)
                else:
                    tmp[id_source] = [revids]
        # source -> list of closest
        lookup = {}
        for k, v in tmp.items():
            lookup[k] = sorted(v, key=lambda x: x.distance)[0:n_neighbors]
        return MultiLookupDistanceCache(lookup=lookup, n_neighbors=n_neighbors)

    @staticmethod
    def from_json(file):
        with open(file, "r") as f:
            d = json.load(f)
        return MultiLookupDistanceCache(**d)

    def to_json(self, file):
        with open(file, "w") as f:
            json.dump(self.dict(), f)

    def __len__(self):
        return len(self.lookup)


class GreedyConnectCache(BaseModel):
    """Cache that can be used by the greedy connection model"""

    connected_cache: SingleLookupDistanceCache = None
    unconnected_cache: MultiLookupDistanceCache = None

    @staticmethod
    def from_workspace(
        workspace,
        unconnected_file="school_cache.json",
        connected_file="fiber_cache.json",
    ):
        connected_cache, unconnected_cache = None, None
        if connected_file is not None:
            # check to see if the file exists
            if os.path.exists(os.path.join(workspace, connected_file)):
                connected_cache = SingleLookupDistanceCache.from_json(
                    os.path.join(workspace, connected_file)
                )
        if unconnected_file is not None:
            # check to see if the file exists
            if os.path.exists(os.path.join(workspace, unconnected_file)):
                unconnected_cache = MultiLookupDistanceCache.from_json(
                    os.path.join(workspace, unconnected_file)
                )
        return GreedyConnectCache(
            connected_cache=connected_cache, unconnected_cache=unconnected_cache
        )

    def __len__(self):
        return len(self.connected_cache or []) + len(self.unconnected_cache or [])
