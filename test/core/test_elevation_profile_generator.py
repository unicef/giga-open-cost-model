import pytest

from pydantic.error_wrappers import ValidationError
from giga.models.nodes.elevation.elevation_profile_generator import (
    ElevationProfileGenerator,
)
from giga.schemas.geo import ElevationProfile, ElevationPoint


@pytest.fixture()
def elevation_profile_generator_model():
    return ElevationProfileGenerator()


@pytest.fixture()
def sample_elevation_data_points():
    data = [[[42.06, 42.37], [-72.61, -72.52]]]
    return data


@pytest.fixture()
def sample_elevation_profile_results():
    results = [
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
    return results


def test_wrong_input_elevation(elevation_profile_generator_model):
    with pytest.raises(ValidationError):
        # string input invalid
        elevation_profile_generator_model.run("1")
    with pytest.raises(ValidationError):
        # single number input invalid
        elevation_profile_generator_model.run(1)
    with pytest.raises(ValidationError):
        # nested list of single numbers invalid
        elevation_profile_generator_model.run([[1], [2]])
    with pytest.raises(ValidationError):
        # list of tuples with mixed size invalid
        elevation_profile_generator_model.run([(1, 1), (1)])


def test_empty_elevation(elevation_profile_generator_model):
    elevations = elevation_profile_generator_model.run([])
    assert elevations == []


def test_elevation_profile_regression_test(
    elevation_profile_generator_model,
    sample_elevation_data_points,
    sample_elevation_profile_results,
):
    elevations = elevation_profile_generator_model.run(
        sample_elevation_data_points, samples=4
    )
    assert elevations == sample_elevation_profile_results
