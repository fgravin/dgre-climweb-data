import logging
import os
import re
from datetime import datetime

import pandas as pd

from dgrehydro import SETTINGS
from dgrehydro import db
from dgrehydro.models.flashflood import FlashFlood
from dgrehydro.utils import get_dates_from_dataframe


def ingest_flash_floods_from_csv() -> list[FlashFlood]:
    data_dir = SETTINGS['DATA_FLASHFLOOD_SOURCE_DIR']
    csv_path = get_last_date_from_filename(data_dir)

    logging.info(f"[INGESTION][FLASHFLOOD][CSV] Load {csv_path}")
    if not os.path.exists(csv_path):
        logging.error(f"[INGESTION][FLASHFLOOD][CSV] CSV file {csv_path} does not exist.")
        raise FileNotFoundError(f"CSV file {csv_path} does not exist.")

    db_flash_floods = extract_db_flash_floods_from_csv(csv_path)

    logging.info("[INGESTION][FLASHFLOOD][CSV]: Ingest in base")
    for db_flash_flood in db_flash_floods:
        db.session.add(db_flash_flood)

    db.session.flush(db_flash_floods)
    db.session.commit()
    logging.info("[INGESTION][FLASHFLOOD][CSV]: Done")


def get_flash_csv_input_path_of_the_day(data_dir) -> str:
    today = datetime.now().strftime("%Y%m%d")
    csv_file_name = f"colorscales_{today}.csv"
    csv_path = os.path.join(data_dir, csv_file_name)
    return csv_path


def extract_db_flash_floods_from_csv(csv_path) -> list[FlashFlood]:
    df = pd.read_csv(csv_path)
    flash_floods = []

    date_cols = get_dates_from_dataframe(df)
    init_date = date_cols[0]

    for _, row in df.iterrows():
        fid = int(row["index"])
        subid = row["SUBID"]
        adm3_fr = row["ADM3_FR"]
        forecast_date = pd.to_datetime(init_date)
        value = int(row[init_date])
        rf = FlashFlood(
            fid=fid,
            subid=subid,
            adm3_fr=adm3_fr,
            forecast_date=forecast_date,
            init_value=value,
            value=value
        )
        flash_floods.append(rf)
    return flash_floods


def get_last_date_from_filename(data_dir: str) -> datetime:
    files = [f for f in os.listdir(data_dir) if f.startswith("colorscales_") and f.endswith(".csv")]
    date_files = []
    for f in files:
        m = re.search(r"colorscales_(\d{4}_\d{2}_\d{2}_\d{2})", f)
        if m:
            dt = datetime.strptime(m.group(1), "%Y_%m_%d_%H")
            date_files.append((dt, f))
    if not date_files:
        raise FileNotFoundError("No matching files found.")
    latest_file = max(date_files, key=lambda x: x[0])[1]
    return os.path.join(data_dir, latest_file)