import json
import logging
import os
import re
from datetime import datetime

import pandas as pd

from dgrehydro import SETTINGS
from dgrehydro import db
from dgrehydro.models.riverineflood import RiverineFlood
from dgrehydro.utils import get_dates_from_dataframe, load_riverine_flood_geojson, get_dates_from_geojson


def ingest_riverine_floods_from_csv() -> list[RiverineFlood]:
    data_dir = SETTINGS['DATA_RIVERINE_SOURCE_DIR']
    csv_path = get_riverine_csv_input_path_of_the_day(data_dir)

    logging.info(f"[INGESTION][RIVERINE][CSV] Load {csv_path}")
    if not os.path.exists(csv_path):
        logging.error(f"[INGESTION][RIVERINE][CSV] CSV file {csv_path} does not exist.")
        raise FileNotFoundError(f"CSV file {csv_path} does not exist.")

    db_riverine_floods = extract_db_riverines_from_csv(csv_path)

    logging.info("[INGESTION][RIVERINE][CSV]: Ingest in base")
    for db_riverine_flood in db_riverine_floods:
        db.session.add(db_riverine_flood)

    db.session.flush(db_riverine_floods)
    db.session.commit()

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


# CSV file extracted from FANFAR data
# index,SUBID,2025-06-27,2025-06-28,2025-06-29,2025-06-30,2025-07-01,2025-07-02,2025-07-03,2025-07-04
# 1,53,0,0,0,0,0,0,0,0
# 2,43,0,0,0,0,0,0,0,0
def extract_db_riverines_from_csv(csv_path) -> list[RiverineFlood]:
    df = pd.read_csv(csv_path)
    riverine_floods = []

    date_cols = get_dates_from_dataframe(df)
    init_date = pd.to_datetime(date_cols[0])

    for _, row in df.iterrows():
        fid = int(row["index"])
        subid = int(row["SUBID"])
        for date_col in date_cols:
            forecast_date = pd.to_datetime(date_col)
            value = int(row[date_col])
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

def ingest_riverine_floods() -> pd.DataFrame:
    logging.info("[INGESTION][RIVERINE]: Start")
    data_dir = SETTINGS['DATA_RIVERINE_SOURCE_DIR']
    all_files = [f for f in os.listdir(data_dir) if "hydrogram" in f]
    last_date = get_last_date_from_filename(all_files)
    hydrograph_files = [f for f in all_files if re.search(r"\d{12}", f) and
                        datetime.strptime(re.search(r"\d{12}", f).group(), "%Y%m%d%H%M") == last_date]

    forecast = None
    for i, file_name in enumerate(hydrograph_files):
        full_path = os.path.join(data_dir, file_name)
        with open(full_path, 'r') as f:
            current_data = json.load(f)

        discharge_str = current_data.get("time_series_discharge_simulated-gfs", "")
        discharge = [float(x) if x != "-9999" else None for x in discharge_str.split(",")]
        time_data = current_data.get("time_period", "").split(",")

        time_series = pd.DataFrame({
            "time": time_data,
            "discharge": discharge
        })

        # Daily average per date (YYYY-MM-DD)
        time_series["date"] = [t[:10] for t in time_series["time"]]
        daily = time_series.groupby("date", as_index=False)["discharge"].mean()
        section_id = current_data.get("section_id", f"section_{i + 1}")
        daily.rename(columns={"discharge": section_id}, inplace=True)

        if forecast is None:
            forecast = daily
        else:
            forecast = pd.merge(forecast, daily, on="date", how="outer")

    return forecast


def get_last_date_from_filename(all_files) -> datetime:
    dates = [re.search(r"\d{12}", f).group() for f in all_files if re.search(r"\d{12}", f)]
    datetimes = [datetime.strptime(date_str, "%Y%m%d%H%M") for date_str in dates]
    return max(datetimes)
