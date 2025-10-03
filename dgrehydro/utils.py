import re

import pandas as pd
import requests

from dgrehydro.errors import WarningsNotFound, WarningsRequestError

date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")


def get_dates_from_dataframe(data_frame: pd.DataFrame):
    date_cols = [col for col in data_frame.columns if date_pattern.match(col)]
    return date_cols

def get_json_warnings(url):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            raise WarningsNotFound(f"Warnings not found for {url}")
        else:
            raise WarningsRequestError(f"Error fetching warnings for {url}")


