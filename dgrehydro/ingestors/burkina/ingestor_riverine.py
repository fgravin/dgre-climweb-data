import logging
import os
import re
from datetime import datetime

import pandas as pd

from dgrehydro import SETTINGS
from dgrehydro import db
from dgrehydro.models.riverineflood import RiverineFlood
from dgrehydro.models.riversegment import RiverSegment
from dgrehydro.utils import load_riverine_flood_geojson, get_dates_from_geojson


def ingest_riverine_floods_from_csv() -> list[RiverineFlood]:
    data_dir = SETTINGS['DATA_RIVERINE_SOURCE_DIR']
    csv_colorscales_path = os.path.join(data_dir, 'colorscales.csv')
    csv_dates_path = os.path.join(data_dir, 'forecast_dates.csv')

    check_csv_path(csv_colorscales_path)
    check_csv_path(csv_dates_path)

    db_riverine_floods = extract_db_riverines_from_csv(csv_colorscales_path, csv_dates_path)

    logging.info("[INGESTION][RIVERINE][CSV]: Ingest in base")
    for db_riverine_flood in db_riverine_floods:
        db.session.add(db_riverine_flood)

    db.session.flush(db_riverine_floods)
    db.session.commit()

def check_csv_path(csv_path):
    logging.info(f"[INGESTION][RIVERINE][CSV] Load {csv_path}")
    if not os.path.exists(csv_path):
        logging.error(f"[INGESTION][RIVERINE][CSV] CSV file {csv_path} does not exist.")
        raise FileNotFoundError(f"CSV file {csv_path} does not exist.")


def ingest_riverine_floods_from_geojson() -> list[RiverineFlood]:
    logging.info("[INGESTION][RIVERINE][GeoJson]: Start")
    logging.info("[INGESTION][RIVERINE][GeoJson]: Load geojson")
    geojson = load_riverine_flood_geojson()

    logging.info("[INGESTION][RIVERINE][GeoJson]: Ingest in base")
    db_flash_floods = extract_riverines_from_geojson(geojson)
    for db_flash_flood in db_flash_floods :
        db.session.add(db_flash_flood)

    db.session.flush(db_flash_floods)
    db.session.commit()

def get_riverine_csv_input_path_of_the_day(data_dir) -> str:
    today = datetime.now().strftime("%Y%m%d")
    csv_file_name = f"colorscales_{today}.csv"
    csv_path = os.path.join(data_dir, csv_file_name)
    return csv_path

def extract_db_riverines_from_csv(csv_colorscales_path, csv_dates_path) -> list[RiverineFlood]:
    df_colorscales = pd.read_csv(csv_colorscales_path)
    df_dates = pd.read_csv(csv_dates_path)
    riverine_floods = []

    day_cols = [col for col in df_colorscales.columns if re.match(r'^day\d+$', col)]
    day_date_map = map_day_date(df_dates)
    init_date = pd.to_datetime(day_date_map[day_cols[0]])

    for _, row in df_colorscales.iterrows():
        fid = int(row["index"])
        subid = str(row["SUBID"])

        db_river_segment = RiverSegment.query.get(subid)
        if db_river_segment is None:
            continue

        for day_col in day_cols:
            date = day_date_map[day_col]
            forecast_date = pd.to_datetime(date)
            value = int(row[day_col])
            rf = RiverineFlood(
                fid=fid,
                subid=subid,
                init_date=init_date,
                forecast_date=forecast_date,
                init_value=value,
                value=value
            )
            riverine_floods.append(rf)
    return riverine_floods

def map_day_date(df):
    mapping = {
        row["Jour"]: row["Date"]
        for _, row in df.iterrows()
        if re.match(r"\d{4}-\d{2}-\d{2}", str(row["Date"]))
    }
    return mapping

def extract_riverines_from_geojson(geojson):
    riverine_floods = []

    forecast_dates = get_dates_from_geojson(geojson)
    init_date = forecast_dates[0]

    for feature in geojson['features']:
        for forecast_date in forecast_dates:
            value = feature['properties'][forecast_date.strftime("%Y-%m-%d")]
            fid = feature['properties']["fid"]
            subid = feature['properties']["SUBID"]
            init_value = value
            rf = RiverineFlood(
                fid=fid,
                subid=subid,
                init_date=init_date,
                forecast_date=forecast_date,
                init_value=init_value,
                value=init_value
            )
            riverine_floods.append(rf)
    return riverine_floods
