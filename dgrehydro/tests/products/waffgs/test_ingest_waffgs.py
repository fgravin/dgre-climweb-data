import os.path

from dgrehydro.config.base import SETTINGS
from dgrehydro.ingestors.flashflood.flash_fetch import fetch_waffgs_data
from dgrehydro.ingestors.flashflood.flash_ingest import ingest_ffgs_data


def test_ingest_hype(monkeypatch):
    monkeypatch.setitem(SETTINGS, 'DATA_DIR', "./resources/")
    ingest_ffgs_data('resources/waffgs/20251008/20251008-1200_ffgs_prod_fcst_fft_forecast1_06hr_regional.txt')
    assert True

