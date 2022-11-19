from pydantic import validate_arguments
from typing import List, Text
from requests.adapters import HTTPAdapter, Retry
import requests

from giga.schemas.geo import LatLonPoint
from giga.compute.elevation.elevation_utilities import (
    format_opendata_request_singular_request,
)

# Constants
DEFAULT_DATASET = "aster30m"
DEFAULT_RETRIES = 5
DEFAULT_BACKOFF = 0.3

# retry on all status codes that are 300+
DEFAULT_FORCELIST = [x for x in requests.status_codes._codes if x >= 300]


class OpenElevationModel:
    """
    Generates an elevation profile for lat/lon points using
    open source data sets.
    """

    def format_data(self, x):
        data_transformed = format_opendata_request_singular_request(x)
        return data_transformed

    def query_elevation_dataset(self, data: List[LatLonPoint], dataset: Text):
        """
        class method that manages the request format
        for interacting with the OpenTopoData
        open dataset

        Input: values: An array of values in the format of
            e.g. lat1, lon1| lat2,lon2

            dataset: The name of the OpenTopoData daatset
            you are interested in e.g. aster30m, nzdem8m for more information
            regarding available datasets visit - https://www.opentopodata.org/
        Output: Response Object containing json reults

        """
        if data == []:
            return []
        else:
            # Format data for request
            values = self.format_data(data)
            # create payload for POST request using formatted values
            params = {"locations": f"{values}"}
            url = f"https://api.opentopodata.org/v1/{dataset}?"
            session = requests.Session()
            retries = Retry(
                total=DEFAULT_RETRIES,
                backoff_factor=DEFAULT_BACKOFF,
                status_forcelist=frozenset(DEFAULT_FORCELIST),
                raise_on_redirect=True,
                raise_on_status=True,
            )
            session.mount("https://", HTTPAdapter(max_retries=retries))
            session.mount("http://", HTTPAdapter(max_retries=retries))
            response = session.post(url, params)
            result = response.json()
            elevation_values_array = [x["elevation"] for x in result["results"]]
            return elevation_values_array

    @validate_arguments
    def run(self, data: List[LatLonPoint], dataset=DEFAULT_DATASET) -> List[float]:
        """
        Input: ordered list of lists or tuples of lat/lon coordinates
               e.g: [[1,2], [3,4]]
        Output: ordered list of elevations for the input coordinates
        """
        elevation_values = self.query_elevation_dataset(data, dataset)
        return elevation_values
