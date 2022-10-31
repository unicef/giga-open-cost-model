from typing import List, Text

from giga.schemas.geo import LatLonPoint


def format_opendata_request_singular_request(array: List[LatLonPoint]) -> Text:
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

def format_opendata_request_multipoint_request(array) -> Text:
    """
    class method that formats the request to match the API 
    spec here: https://www.opentopodata.org/api/ 

      Input: array: An array of values in the format of 
        e.g. [(lat1, lon1), (lat2,lon2)]   
      Output: transformed list into formatted text   
    """
    # transform array values to (lat, long)|(lat, long) format
    data = str(array).replace('],', '|')\
    .replace('[[', "")\
    .replace(']]', "")\
    .replace('[', "")\
    .strip()

    return data