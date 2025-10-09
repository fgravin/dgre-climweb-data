import pandas as pd

from dgrehydro.ingestors.hype.hype_io import read_time_output
from dgrehydro.ingestors.hype.process_hype import process_hype_data


def test_process_hype():
    result = process_hype_data()
    assert result is True

def test_read_time_output():
    dataframe = read_time_output('./resources/hype/r20251006_1049_i20251006_forecast_timeCOUT.txt')
    expected = pd.read_csv('./resources/hype/forecast.csv')
    assert dataframe.equals(expected) is True
