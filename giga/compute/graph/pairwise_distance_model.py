from typing import List, Tuple
import numpy as np
from haversine import haversine
from pydantic import validate_arguments

from giga.schemas.geo import UniqueCoordinate, PairwiseDistance
from giga.utils.progress_bar import progress_bar


DEFAULT_DISTANCE_FN = lambda x, y: haversine(x, y, unit='m')

class PairwiseDistanceModel:
    
    def __init__(self, **kwargs):
        self.distance_fn = kwargs.get('distance_fn', DEFAULT_DISTANCE_FN)
        self.progress_bar = kwargs.get('progress_bar', False)
        
    @validate_arguments
    def run_matrix(self, data: List[UniqueCoordinate], **kwargs) -> List[PairwiseDistance]:
        # TODO: this could be moved into a separate model in a future refactor
        pairs = []
        iterable = progress_bar(data) if self.progress_bar else data
        for i, c1 in enumerate(iterable):
            for c2 in data[i+1:]:
                dist = self.distance_fn(c1.coordinate, c2.coordinate)
                pairs.append(PairwiseDistance(pair_ids=(c1.coordinate_id, c2.coordinate_id),
                                              coordinate1=c1,
                                              coordinate2=c2,
                                              distance=dist))
        return pairs

    @validate_arguments
    def run(self, data: Tuple[List[UniqueCoordinate], List[UniqueCoordinate]], **kwargs) -> List[PairwiseDistance]:
        set1, set2 = data
        pairs = []
        iterable = progress_bar(set1) if self.progress_bar else set1
        for i, c1 in enumerate(iterable):
            for c2 in set2:
                dist = self.distance_fn(c1.coordinate, c2.coordinate)
                pairs.append(PairwiseDistance(pair_ids=(c1.coordinate_id, c2.coordinate_id),
                                              coordinate1=c1,
                                              coordinate2=c2,
                                              distance=dist))
        return pairs
