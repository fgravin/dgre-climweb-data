from datetime import datetime

from dgrehydro.ingestors.hype.hype_fetch import fetch_daily_hype_data
from dgrehydro.config.base import SETTINGS

def test_fetch_hype(monkeypatch):
    monkeypatch.setitem(SETTINGS, 'DATA_DIR', "./resources/fanfar")
    result = fetch_daily_hype_data(datetime(2026, 1, 21))
    assert result is True

