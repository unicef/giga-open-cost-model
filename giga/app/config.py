import os
from hydra import compose, initialize
from typing import List
from omegaconf import DictConfig


# Use to update the baseline application configurations
CONFIG_PATH = "../../conf"
CONFIG_NAME = "config"

# Global configuration init happens here
initialize(version_base=None, config_path=CONFIG_PATH)


def get_config(overrides: List[str] = []):
    return compose(config_name=CONFIG_NAME, overrides=overrides)


class ConfigClient:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg

    @property
    def school_file(self):
        file = os.path.join(
            self.cfg.data.workspace,
            self.cfg.data.country_workspace,
            self.cfg.data.school_file,
        )
        return file

    @property
    def fiber_file(self):
        file = os.path.join(
            self.cfg.data.workspace,
            self.cfg.data.country_workspace,
            self.cfg.data.fiber_file,
        )
        return file

    @property
    def cellular_file(self):
        file = os.path.join(
            self.cfg.data.workspace,
            self.cfg.data.country_workspace,
            self.cfg.data.cellular_file,
        )
        return file
