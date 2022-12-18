from enum import Enum


class ConnectivityTechnology(str, Enum):
    """Technologies that can be assessed in modeling scenarios"""

    fiber = "Fiber"
    cellular = "Cellular"
    sattelitle = "Satellite"
    none = "None"
