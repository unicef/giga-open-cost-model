from pydantic import validate_arguments
from typing import List, Text

import requests
from requests.adapters import HTTPAdapter, Retry

from giga.models.nodes.elevation.elevation_utilities import (
    format_opendata_request_multipoint_request,
)
from giga.schemas.geo import LatLonPoint, RawElevationPoint, ElevationProfile

# Constants
NUMBER_OF_SAMPLES = 10
DEFAULT_DATASET = "aster30m"
DEFAULT_RETRIES = 5
DEFAULT_BACKOFF = 0.3

# retry on all status codes that are 300+
DEFAULT_FORCELIST = [x for x in requests.status_codes._codes if x >= 300]


class ElevationProfileGenerator:
    """
    Generates an elevation profile for lat/lon points using
    open source data sets.

    """

    def format_data(self, data: List) -> Text:
        transformer = lambda x: format_opendata_request_multipoint_request(x)
        data_transformed = transformer(data)
        return data_transformed

    def query_elevation_dataset(self, data: List, dataset: Text, samples: int) -> List:
        """
        class method that manages the request format
        for interacting with the OpenTopoData
        open dataset

        Input: values: An array of geomteric points (start and endpoints) in the
                       format of e.g. lat1, lon1| lat2,lon2

            dataset: The name of the OpenTopoData daatset
            you are interested in e.g. aster30m, nzdem8m for more information
            regarding available datasets visit - https://www.opentopodata.org/
        Output: Response Object containing json reults

        """
        elevation_profile_list = list()
        for points in data:
            if points == []:
                elevation_profile_list.append([])
            else:
                # Format data for request
                values = self.format_data(points)
                # create payload for POST request using formatted values
                params = {"locations": f"{values}", "samples": f"{samples}"}
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
                result = response.json()["results"]
                result_transformed = RawElevationPoint.elevation_point_transformer(
                    result
                )
                ele_profile = ElevationProfile.from_raw_elevation_profile(
                    result_transformed
                )
                elevation_profile_list.append(ele_profile)
        return elevation_profile_list

    @validate_arguments
    def run(
        self,
        data: List[List[LatLonPoint]],
        dataset: Text = DEFAULT_DATASET,
        samples: int = NUMBER_OF_SAMPLES,
    ) -> List[ElevationProfile]:
        """
        Input: ordered list of lists of lat/lon coordinates
               e.g: [[1,2], [3,4]]
        Output: ordered list of elevation profiles for the input coordinates
        """
        results = self.query_elevation_dataset(data, dataset, samples)
        return results
