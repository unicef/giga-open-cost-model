import pytest
from pydantic.error_wrappers import ValidationError

from giga.models.nodes.elevation.open_elevation_model import OpenElevationModel


@pytest.fixture
def elevation_model():
    return OpenElevationModel()


@pytest.fixture()
def sample_data_points():
    data = [(42.06, 42.37), (42.39, 42.42)]
    return data


@pytest.fixture()
def sample_elevation_array_results():
    results = [153.0, 289.0]
    return results


def test_wrong_input_elevation(elevation_model):
    with pytest.raises(ValidationError):
        # string input invalid
        elevation_model.run("1")
    with pytest.raises(ValidationError):
        # single number input invalid
        elevation_model.run(1)
    with pytest.raises(ValidationError):
        # list of single number invalid
        elevation_model.run([1])
    with pytest.raises(ValidationError):
        # list of tuples with mixed size invalid
        elevation_model.run([(1, 1), (1)])


def test_empty_elevation(elevation_model):
    elevations = elevation_model.run([])
    assert elevations == []


def test_open_elevation_regression_test(
    elevation_model, sample_data_points, sample_elevation_array_results
):
    elevations = elevation_model.run(sample_data_points)
    assert elevations == sample_elevation_array_results
