from giga.schemas.conf.data import DataSpaceConf
from giga.data.space.data_space_builders import build_fiber_map, build_school_table


class ModelDataSpace:

    def __init__(self, config: DataSpaceConf):
        self.config = config
        self._schools = None
        self._fiber_map = None

    @property
    def schools(self):
        if self._schools is None:
            # make schools
            self._schools = build_school_table(self.config)
        return self._schools

    @property
    def school_coordinates(self):
        return self.schools.to_coordinates()

    @property
    def fiber_map(self):
        if self._fiber_map is None:
            # make map
            self._fiber_map = build_fiber_map(self.config)
        return self._fiber_map

    @property
    def fiber_coordinates(self):
        return self.fiber_map.coordinates
