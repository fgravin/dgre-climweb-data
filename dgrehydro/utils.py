import json
import logging
import re
import os

from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/data"

def get_dates_from_geojson(geojson):
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    dates = set()
    for feature in geojson['features']:
        for key in feature['properties']:
            if date_pattern.fullmatch(key):
                dates.add(datetime.strptime(key, "%Y-%m-%d"))
    return sorted(dates) if dates else None

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




