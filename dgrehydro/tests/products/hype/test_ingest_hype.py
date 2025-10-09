from dgrehydro.ingestors.hype.hype_fetch import fetch_daily_hype_data, HYPE_MODELS
from dgrehydro.config.base import SETTINGS
from dgrehydro.ingestors.hype.process_hype import process_hype_data


def test_ingest_hype(monkeypatch):
    monkeypatch.setitem(SETTINGS, 'DATA_DIR', "../data")
    result = process_hype_data(HYPE_MODELS[4].get('path'), '20251009')
    assert result is True

