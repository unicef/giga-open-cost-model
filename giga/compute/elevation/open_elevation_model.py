from pydantic import validate_arguments
from typing import List, Text

import requests
import pandas as pd


from giga.schemas.geo import LatLonPoint

# Constants 
DEFAULT_DATASET = 'aster30m'

class OpenElevationModel:
    """
        Generates an elevation profile for lat/lon points using
        open source data sets. 
    """
    
    def _format_data(self, array: List[LatLonPoint]) -> Text:
        """
        class method that formats the request to match the API 
        spec here: https://www.opentopodata.org/api/ 
        
          Input: array: An array of values in the format of 
            e.g. [(lat1, lon1), (lat2,lon2)]   
          Output: transformed list into formatted text   
        """
        # transform array values to (lat, long)|(lat, long) format
        data = str(set(array))\
        .replace('),', '|')\
        .replace('{(', "")\
        .replace(')}', "")\
        .replace('(', "")\
        .strip()
        
        return data
    
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
        # Format data for request
        values = self._format_data(data)    
        # create payload for POST request using formatted values
        params = {'locations': f"{values}"}
        url = f'https://api.opentopodata.org/v1/{dataset}?'
        try:
            response = requests.post(url, params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:",errh)
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:",errc)
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:",errt)
        except requests.exceptions.RequestException as err:
            print ("OOps: Something Else",err)
        
        result = response.json()
        elevation_values_array = [x['elevation'] for x in result['results']]
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
