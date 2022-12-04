from giga.schemas.conf.data import DataSpaceConf


class ModelDataSpace:

    """
    Client for providing the necessary external data needed to drive the cost models
    """

    def __init__(self, config: DataSpaceConf):
        self.config = config
        self._schools = None
        self._fiber_map = None

    @property
    def schools(self):
        if self._schools is None:
            # make schools
            self._schools = self.config.school_data_conf.load()
        return self._schools

    @property
    def school_coordinates(self):
        return self.schools.to_coordinates()

    @property
    def fiber_map(self):
        if self._fiber_map is None:
            # make map
            self._fiber_map = self.config.fiber_map_conf.load()
        return self._fiber_map

    @property
    def fiber_coordinates(self):
        return self.fiber_map.coordinates
