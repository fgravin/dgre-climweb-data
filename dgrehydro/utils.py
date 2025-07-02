import json
import logging
import re
import os
import pandas as pd

from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/data"
date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

def get_dates_from_geojson(geojson):
    dates = set()
    for feature in geojson['features']:
        for key in feature['properties']:
            if date_pattern.fullmatch(key):
                dates.add(datetime.strptime(key, "%Y-%m-%d"))
    return sorted(dates) if dates else None

def get_dates_from_dataframe(data_frame: pd.DataFrame):
    date_cols = [col for col in data_frame.columns if date_pattern.match(col)]
    return date_cols


def load_riverine_flood_geojson():

    if not os.path.exists(DATA_DIR):
        logging.info("[DATA LOADING]: Data directory does not exist")
        return

    geojson_file = os.path.join(DATA_DIR, "riverive_flood_20250525.json")

    if not os.path.exists(geojson_file):
        logging.info(f"[DATA LOADING]: File {geojson_file} does not exist")
        return

    with open(geojson_file, "r") as f:
        geojson = json.load(f)
        return geojson




