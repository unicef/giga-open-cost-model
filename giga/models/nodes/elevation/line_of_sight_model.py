from pydantic import validate_arguments
from typing import List, Text
from haversine import haversine, Unit
from shapely.geometry import Point, LineString
from giga.schemas.geo import LatLonPoint, ElevationProfile

DEFAULT_BUFFER = 0.0


class LineofSightModel:
    """
    Classs that determines the current line of sight for a given set of cooridnates
    based on the elevation profile
    """

    def create_buffered_profile(
        self, elevation_array: List, elevation_buffer_meters: float
    ) -> List:
        """
        class method that accepts an elevation array of float values
        and returns an adjusted array of float values based on buffer
        set by user

            Input:
                elevation_array: An array of elevation values
                elevation_buffer_meters: Integer value controlling upper boundary of elevation values
                between starting and end points
            Output: Updated array of elevation values
        """
        updated_elevations = [x + elevation_buffer_meters for x in elevation_array]
        # remove buffer val from beginning and end points
        updated_elevations[0] = updated_elevations[0] - elevation_buffer_meters
        updated_elevations[-1] = updated_elevations[-1] - elevation_buffer_meters
        return updated_elevations

    def get_elevations(self, elevation_profile: ElevationProfile) -> List:
        """
        class method that generates an array of elevation values

            Input:
                elevation_profile : Nested Dictionary (Response from OpenData API)
            Output: Ordered array of elevation float values
        """
        ele_arr = [x.elevation for x in elevation_profile]
        return [0 if i is None else i for i in ele_arr]

    def get_coordinates(self, elevation_profile: ElevationProfile) -> List:
        """
        class method that generates an array of coordinate pairs

            Input: List
            Output: List
        """
        coordinates = [x.coordinates for x in elevation_profile]
        return coordinates

    def calculate_distance(self, coordinates: List) -> List:
        """
        class method that generates an array of distance values based on the Haversine formula

            Input: List
            Output: List
        """
        start = coordinates[0]
        return [haversine(start, x, unit=Unit.METERS) for x in coordinates]

    def determine_obstructions(
        self, elevation_profile: ElevationProfile, elevation_buffer_meters: float
    ) -> List:
        """
        class method that generates an array of boolean values based on line of sight availability

            Input:
                elevation_profile: singluar elevation profile
                elevation_buffer_meters: Integer value to increase or decrease upper bound of elevation values
            Output: Boolean value
        """
        elevations_array = self.create_buffered_profile(
            self.get_elevations(elevation_profile),
            elevation_buffer_meters=elevation_buffer_meters,
        )
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
    def run(
        self,
        elevation_profiles: List[ElevationProfile],
        elevation_buffer_meters: float = DEFAULT_BUFFER,
    ) -> List[bool]:
        """
        Class method that determines whether the line of sight is obstructed,
        given a collection of elevation profiles. Each elevation profile in the collection
        is iterated through and generates a singular profile which recieves a True of False flag
        if line of sight is obscured.

            Input:
                elevation_profiles: a collection of elevation profiles
                elevation_buffer_meters: Integer value to increase or decrease upper bound of elevation values
            Output: Orderd array of boolean values
        """
        line_of_sight_array = []
        for profiles in elevation_profiles:
            line_of_sight_array.append(
                self.determine_obstructions(
                    profiles.points, elevation_buffer_meters=elevation_buffer_meters
                )
            )
        return line_of_sight_array
