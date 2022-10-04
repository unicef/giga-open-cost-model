import pytest
from pydantic.error_wrappers import ValidationError

from giga.compute.elevation.open_elevation_model import OpenElevationModel


@pytest.fixture
def elevation_model():
    return OpenElevationModel()

def test_wrong_input_elevation(elevation_model):
    with pytest.raises(ValidationError):
        # string input invalid
        elevation_model.run('1')
    with pytest.raises(ValidationError):
        # single number input invalid
        elevation_model.run(1)
    with pytest.raises(ValidationError):
        # list of single number invalid
        elevation_model.run([1])
    with pytest.raises(ValidationError):
        # list of tuples with mixed size invalid
        elevation_model.run([(1,1), (1)])

def test_empty_elevation(elevation_model):
    elevations = elevation_model.run([])
    assert elevations == []
