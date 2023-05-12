from pydantic import validate_arguments
from typing import List, Text

import requests
import time
from requests.adapters import HTTPAdapter, Retry

from giga.models.nodes.elevation.elevation_utilities import (
    format_opendata_request_multipoint_request,
)
from giga.schemas.geo import LatLonPoint, RawElevationPoint, ElevationProfile

# Constants
NUMBER_OF_SAMPLES = 10
DEFAULT_DATASET = "aster30m"
DEFAULT_RETRIES = 5
DEFAULT_BACKOFF = 1.0

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
        Queries the opentopodata API to create an elevation profile
        A profile is a collection of ordered 3D points including lat/lon and elevation values

        :param data, list of lat/lon points between which elevation profiles are created
        :param dataset, the type of elevation dataset to query, generally aster30m
        :param samples, the number of elevation samples to include in the profile in addition to the two root points
        :returns List of elevation profiles (e.g. a list of lists of 3D points)
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
                if "results" not in response.json():
                    raise RuntimeError(
                        f"Unexpected OpenTopoData API response: {response.json()}"
                    )
                result = response.json()["results"]
                result_transformed = RawElevationPoint.elevation_point_transformer(
                    result
                )
                ele_profile = ElevationProfile.from_raw_elevation_profile(
                    result_transformed
                )
                elevation_profile_list.append(ele_profile)
                # TODO: This is added to avoid rate-limiting failures (1/sec).
                #       We should batch the requests better (it supports <=100 locations/req).
                time.sleep(0.9)
        return elevation_profile_list

    @validate_arguments
    def run(
        self,
        data: List[List[LatLonPoint]],
        dataset: Text = DEFAULT_DATASET,
        samples: int = NUMBER_OF_SAMPLES,
    ) -> List[ElevationProfile]:
        """
        Runs the elevation profile generator model.
        :param data, ordered list of lists of lat/lon coordinates e.g: [[1,2], [3,4]]
        :param dataset, the type of elevation dataset to query, defaults to aster30m
        :param samples, the number of elevation samples to include in the profile in addition to the two root points
               defaults to 10
        :return a list of elevation profiles (e.g. a list of lists of 3D points)
        """
        results = self.query_elevation_dataset(data, dataset, samples)
        return results
