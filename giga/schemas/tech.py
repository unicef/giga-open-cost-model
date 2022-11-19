from enum import Enum
from pydantic import BaseModel


class ConnectivityTechnology(str, Enum):
    """Technologies that can be assessed in modeling scenarios"""

    fiber = "Fiber"
    cellular = "Cellular"
    sattelitle = "Satellite"
