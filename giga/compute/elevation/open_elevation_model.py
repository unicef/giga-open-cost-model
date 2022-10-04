from pydantic import validate_arguments
from typing import List

from giga.schemas.geo import LatLonPoint


class OpenElevationModel:
    """
        Generates an elevation profile for lat/lon points using
        open source data sets. 
    """

    def __init__(self):
        pass

    @validate_arguments
    def run(self, data: List[LatLonPoint]) -> List[float]:
        """
            Input: ordered list of lists or tuples of lat/lon coordinates
                   e.g: [[1,2], [3,4]]
            Output: ordered list of elevations for the input coordinates
        """
        return [] # TODO: update with a real implementation
