import datetime
import os

import pytest

from dgrehydro.ingestors.burkina.ingestor_riverine import get_last_date_from_filename, \
    get_riverine_csv_input_path_of_the_day, extract_db_riverines_from_csv, extract_riverines_from_geojson


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
                    "2025-05-24":30,
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
    csv_path = get_riverine_csv_input_path_of_the_day('/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/wl')
    assert csv_path is not None
    assert csv_path == '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/wl/colorscales_' + datetime.datetime.now().strftime("%Y%m%d") + '.csv'

def test_get_last_date_from_filenames():
    data_dir = '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci'
    all_files = [f for f in os.listdir(data_dir) if "hydrogram" in f]
    last_date = get_last_date_from_filename(all_files)
    assert last_date is not None
    assert last_date.year == 2025
    assert last_date == datetime.datetime(2025, 6, 29, 0, 0)  # Adjust this based on the actual last date in your test data

def test_extract_db_riverines_from_csv():
    csv_path = '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/wl/colorscales_20250618.csv'
    results = extract_db_riverines_from_csv(csv_path)
    assert isinstance(results, list)
    assert len(results) == 520
    for obj in results:
        assert hasattr(obj, "fid")
        assert hasattr(obj, "subid")
        assert hasattr(obj, "init_date")
        assert hasattr(obj, "forecast_date")
        assert hasattr(obj, "value")
        assert hasattr(obj, "init_value")
    assert results[0].init_date == datetime.datetime(2025, 6, 16)
    assert results[0].forecast_date == datetime.datetime(2025, 6, 16)
    assert results[0].init_value == 30
    assert results[0].value == 30

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
