import pytest

from giga.schemas.school import GigaSchoolTable


@pytest.fixture
def single_school_sample():
    return {'school_id': '33062501',
            'name': '0101001 ESCOLA MUNICIPAL VICENTE LICINIO CARDOSO',
            'lon': -43.1837,
            'lat': -22.8971,
            'education_level': '',
            'environment': 'urban',
            'country_id': 144,
            'country': 'Brazil',
            'admin_2_name': '',
            'admin_3_name': '',
            'admin_4_name': 'RIO DE JANEIRO',
            'admin_1_name': 'RIO DE JANEIRO',
            'giga_id_school': '63955a91-d652-3bce-97af-72918cb4259b'}

@pytest.fixture
def school_table_sample(single_school_sample):
    return GigaSchoolTable(schools=[single_school_sample])

def test_data_model_creation(single_school_sample):
    table = GigaSchoolTable(schools=[single_school_sample])
    assert table.schools[0].school_id == '33062501'
    assert table.schools[0].giga_id == '63955a91-d652-3bce-97af-72918cb4259b'

def test_table_to_coordinate_conversion(school_table_sample):
    coordinates = school_table_sample.to_coordinates()
    coordinates[0].coordinate_id == '63955a91-d652-3bce-97af-72918cb4259b'
    coordinates[0].coordinate == [-22.8971, -43.1837]
