import os.path

from dgrehydro.config.base import SETTINGS
from dgrehydro.ingestors.flashflood.flash_fetch import fetch_waffgs_data
from dgrehydro.ingestors.flashflood.flash_ingest import ingest_ffgs_data


def test_process_hype(monkeypatch):
    monkeypatch.setitem(SETTINGS, 'DATA_DIR', "./resources/")
    filename = fetch_waffgs_data()
    ingest_ffgs_data(filename)
    assert os.path.relpath(filename) == 'resources/waffgs/20251008/20251008-1200_ffgs_prod_fcst_fft_forecast1_06hr_regional.txt'

