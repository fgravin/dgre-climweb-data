import os

from dgrehydro.ingestors.burkina.ingestor_flashflood import get_last_date_from_filename


def test_get_last_date_from_filename():
    data_dir = '/home/fgravin/dev/perso/wmo/dgre-climweb-data/sapci/flashflood/wl'
    last_file = get_last_date_from_filename(data_dir)
    assert last_file is not None
