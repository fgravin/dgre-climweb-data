from dgrehydro.config.base import SETTINGS
from dgrehydro.ingestors.process_floodproofs import get_matching_files, process_hydrographs
import os


def test_process_hydrographs(monkeypatch):
    resources_path = os.path.join(os.path.dirname(__file__), "../resources/floodproof")
    absolute_path = os.path.abspath(resources_path)
    monkeypatch.setitem(SETTINGS, 'FLOODPROOF_DATA_DIR', absolute_path)

    process_hydrographs('202505160000')

def test_get_matching_files(monkeypatch):
    resources_path = os.path.join(os.path.dirname(__file__), "../resources/floodproof")
    absolute_path = os.path.abspath(resources_path)

    monkeypatch.setitem(SETTINGS, 'FLOODPROOF_DATA_DIR', absolute_path)
    files = get_matching_files('202505150000')
    assert len(files) == 2
