import pytest

from pydantic.error_wrappers import ValidationError
from giga.models.nodes.elevation.line_of_sight_model import LineofSightModel
from giga.schemas.geo import ElevationProfile, ElevationPoint


@pytest.fixture()
def line_of_sight_model():
    return LineofSightModel()


@pytest.fixture()
def sample_elevation_data_points():
    data = [
        ElevationProfile(
            points=[
                ElevationPoint(coordinates=(42.06, 42.37), elevation=289.0),
                ElevationPoint(
                    coordinates=(-1.2293237828648182, 25.819056664864316),
                    elevation=493.0,
                ),
                ElevationPoint(
                    coordinates=(-44.40109930085374, 8.601711803089884), elevation=None
                ),
                ElevationPoint(coordinates=(-72.61, -72.52), elevation=0.0),
            ]
        )
    ]
    return data


@pytest.fixture()
def sample_line_of_sight_model_response():
    response = [True]
    return response


@pytest.fixture()
def elevation_buffer_value():
    val = 100
    return val


@pytest.fixture()
def sample_line_of_sight_model_updated_buffer_failure_response():
    response = [False]
    return response


def test_wrong_input_elevation(line_of_sight_model):
    with pytest.raises(ValidationError):
        # string input invalid
        line_of_sight_model.run("1")
    with pytest.raises(ValidationError):
        # single number input invalid
        line_of_sight_model.run(1)
    with pytest.raises(ValidationError):
        # nested list of single numbers invalid
        line_of_sight_model.run([[1], [2]])
    with pytest.raises(ValidationError):
        # list of tuples with mixed size invalid
        line_of_sight_model.run([(1, 1), (1)])


def test_empty_elevation(line_of_sight_model):
    result_set = line_of_sight_model.run([])
    assert result_set == []


def test_light_of_sight_regression_test(
    line_of_sight_model,
    sample_elevation_data_points,
    sample_line_of_sight_model_response,
):
    result = line_of_sight_model.run(sample_elevation_data_points)
    assert result == sample_line_of_sight_model_response


def test_light_of_sight_buffer_failed_regression_test(
    line_of_sight_model,
    sample_elevation_data_points,
    sample_line_of_sight_model_updated_buffer_failure_response,
    elevation_buffer_value,
):
    result = line_of_sight_model.run(
        sample_elevation_data_points, elevation_buffer_meters=elevation_buffer_value
    )
    assert result == sample_line_of_sight_model_updated_buffer_failure_response
