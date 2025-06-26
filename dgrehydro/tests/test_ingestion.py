import datetime

import pytest

from dgrehydro.ingestion import explode_geojson_to_riverineflood

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

def test_explode_geojson_to_riverineflood(geojson_data):
    results = explode_geojson_to_riverineflood(geojson_data)
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
    assert results[0].value == 30
    assert results[0].init_value == 30
