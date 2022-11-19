from copy import deepcopy
import os

from giga.schemas.geo import UniqueCoordinateTable
from giga.schemas.school import GigaSchoolTable
from giga.schemas.conf.data import DataSpaceConf, UploadedCoordinateMapConf, LocalWorkspaceTransportConf


def build_school_table(config: DataSpaceConf) -> GigaSchoolTable:
    if type(config.school_data_conf.transport) == LocalWorkspaceTransportConf:
        school_file = os.path.join(config.school_data_conf.transport.workspace, config.school_data_conf.transport.file_name)
        return GigaSchoolTable.from_csv(school_file)

def build_fiber_map(config: DataSpaceConf) -> UniqueCoordinateTable:
    if type(config.fiber_map_conf) == UploadedCoordinateMapConf:
        return deepcopy(config.fiber_map_conf.coordinate_map)
    else:
        return UniqueCoordinateTable(coordinates=[])