import datetime
import os
from unittest.mock import Mock

import geopandas as gpd
import pandas as pd
import pytest

from dgrehydro.ingestors.burkina.ingestor_riverine import get_riverine_csv_input_path_of_the_day, \
    extract_db_riverines_from_csv, extract_riverines_from_geojson, map_day_date


@pytest.fixture
def geojson_data():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "fid": 1,
                    "SUBID": "210048",
                    "2025-05-25": 0,
                    "2025-05-24": 30,
                    "2025-05-26": 1,
                    "2025-05-27": 1,
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[[1.0, 2.0], [3.0, 4.0]]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "fid": 2,
                    "SUBID": "210048",
                    "2025-05-25": 5,
                    "2025-05-24": 3,
                    "2025-05-26": 1,
                    "2025-05-27": 1,
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[[1.0, 2.0], [3.0, 4.0]]]
                }
            }
        ]
    }


def test_get_current_date_csv_path():
    csv_path = get_riverine_csv_input_path_of_the_day(
        '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/riverineflood/wl')
    assert csv_path is not None
    assert csv_path == '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/riverineflood/wl/colorscales_' + datetime.datetime.now().strftime(
        "%Y%m%d") + '.csv'


def test_extract_db_riverines_from_csv(mocker):
    data_dir = '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/riverineflood/'
    csv_colorscales_path = os.path.join(data_dir, 'colorscales.csv')
    csv_dates_path = os.path.join(data_dir, 'forecast_dates.csv')

    class MockQuery:
        def __init__(self, subid):
            self.subid = subid
        def get(self):
            db_river_segment = Mock()
            db_river_segment.subid = self.subid
            return db_river_segment

    class MockRiverSegment:
        def __init__(self, subid):
            self.subid = subid
        def query(self):
            return MockQuery(self.subid)

    mock_rs = MockQuery("210048")

    mock_riverine_flood_class = mocker.patch('dgrehydro.models.riversegment.RiverineFlood', autospec=True)
    mock_instance = mock_riverine_flood_class.return_value
    mock_instance.id = 1
    mock_instance.fid = 1
    mock_instance.subid = "sub1"
    mock_instance.init_date = datetime.now()
    mock_instance.forecast_date = datetime.now()
    mock_instance.init_value = 100
    mock_instance.value = 200
    mock_query = mocker.Mock()
    mock_query.get.return_value = mock_instance
    mock_riverine_flood_class.query = mock_query

    results = extract_db_riverines_from_csv(csv_colorscales_path, csv_dates_path)

    assert isinstance(results, list)
    assert len(results) == 3240
    for obj in results:
        assert hasattr(obj, "fid")
        assert hasattr(obj, "subid")
        assert hasattr(obj, "init_date")
        assert hasattr(obj, "forecast_date")
        assert hasattr(obj, "value")
        assert hasattr(obj, "init_value")

    assert results[0].init_date == datetime.datetime(2025, 7, 1)
    assert results[0].forecast_date == datetime.datetime(2025, 7, 1)
    assert results[0].init_value == 30
    assert results[0].value == 30

    assert results[9].init_date == datetime.datetime(2025, 7, 1)
    assert results[9].forecast_date == datetime.datetime(2025, 7, 10)
    assert results[9].init_value == 50
    assert results[9].value == 50


def test_map_day_date():
    data_dir = '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/riverineflood/'
    csv_dates_path = os.path.join(data_dir, 'forecast_dates.csv')

    df_dates = pd.read_csv(csv_dates_path)
    mapping = map_day_date(df_dates)

    assert isinstance(mapping, dict)
    assert len(mapping) > 0
    assert "day1" in mapping
    assert "2025-07-03" in mapping.values()  # Adjust based on your test data
    assert mapping["day1"] == "2025-07-01"  # Adjust based on your test data
    assert mapping["day10"] == "2025-07-10"  # Adjust based on your test data


def test_extract_riverines_from_geojson(geojson_data):
    results = extract_riverines_from_geojson(geojson_data)
    assert isinstance(results, list)
    assert len(results) == 8
    for obj in results:
        assert hasattr(obj, "fid")
        assert hasattr(obj, "subid")
        assert hasattr(obj, "init_date")
        assert hasattr(obj, "forecast_date")
        assert hasattr(obj, "value")
        assert hasattr(obj, "init_value")
    assert results[0].init_date == datetime.datetime(2025, 5, 24)
    assert results[0].forecast_date == datetime.datetime(2025, 5, 24)
    assert results[0].init_value == 30
    assert results[0].value == 30


def test_run():
    shapefile_path = "/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/flashflood/static/test_vigi_bf_com.shp"
    geojson_path = "/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/flashflood/static/test_vigi_bf_com.geojson"
    gdf = gpd.read_file(shapefile_path)
    gdf.to_file(geojson_path, driver='GeoJSON')
