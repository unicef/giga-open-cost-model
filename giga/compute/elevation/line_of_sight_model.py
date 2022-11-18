from pydantic import validate_arguments
from typing import List, Text
from haversine import haversine, Unit
from shapely.geometry import Point, LineString

import numpy as np


class LineofSightModel:
    """
    Classs that determines the current line of sight for a given set of cooridnates 
    based on the elevation profile
    """

    def get_elevations(self, elevation_profile: List) -> List:
        """
        class method that generates an array of elevation values
        
            Input: 
                elevation_profile : Nested Dictionary (Response from OpenData API)
                buffer: Integer value to increase or decrease upper bound of elevation values
            Output: Ordered array of elevation float values
        """
        ele_arr = [x["elevation"] for x in elevation_profile["results"]]
        return [0 if i is None else i for i in ele_arr]

    def get_coordinates(self, elevation_profile: List) -> List:
        """
        class method that generates an array of coordinate pairs
        
            Input: List
            Output: List
        """
        lat_arr = [x["location"]["lat"] for x in elevation_profile["results"]]
        lng_arr = [x["location"]["lng"] for x in elevation_profile["results"]]
        coordinates = list(zip(lat_arr, lng_arr))
        return coordinates

    def calculate_distance(self, coordinates: List) -> List:
        """
        class method that generates an array of distance values based on the Haversine formula
        
            Input: List
            Output: List
        """
        start = coordinates[0]
        return [haversine(start, x, unit=Unit.METERS) for x in coordinates]

    def determine_obstructions(self, elevation_profile: List) -> List:
        """
        class method that generates an array of boolean values based on line of sight availability 
        
            Input: List
            Output: List
        """
        elevations_array = self.get_elevations(elevation_profile)
        coords_array = self.get_coordinates(elevation_profile)
        distance_array = self.calculate_distance(coords_array)

        coordinates_combined = list(zip(distance_array, elevations_array))
        start_and_endpoints = LineString(
            [Point(coordinates_combined[0]), Point(coordinates_combined[-1])]
        )
        elevation_profile = LineString(coordinates_combined[1:-1])
        
        if start_and_endpoints.intersects(elevation_profile):
            return True
        else:
            return False

    @validate_arguments
    def run(self, elevation_profiles: List) -> List:
        """
        Class method that determines whether the line of sight is obstructed, 
        given a collection of elevation profiles. Each elevation profile in the collection 
        is iterated through and generates a singular profile which recieves a True of False flag
        if line of sight is obscured. 
        
            Input: a collection of elevation profiles 
            Output: Orderd array of boolean values
        """
        for profiles in elevation_profiles:
            line_of_sight = self.determine_obstructions(profiles)
        return line_of_sight
