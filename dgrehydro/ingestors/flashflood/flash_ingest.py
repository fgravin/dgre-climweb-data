import logging
import os

import geopandas as gpd
import numpy as np
import pandas as pd

from dgrehydro import SETTINGS, db
from dgrehydro.models.flashflood import FlashFlood
from dgrehydro.utils import get_dates_from_dataframe

STATIC_DATA_DIR='./dgrehydro/_static_data/'

def assign_vigilance(value):
    if value == 0:
        return 0
    elif value < 10:
        return 1
    elif value < 30:
        return 2
    else:
        return 3

def extract_ffgs_from_source(file_path) -> pd.DataFrame:
    try:
        static_folder = os.path.join(SETTINGS['STATIC_DATA_DIR'], "waffgs")

        ffft_df = pd.read_csv(file_path, delimiter="\t")
        coverage = pd.read_csv(os.path.join(static_folder, "municipality_watershed_coverage.csv"))
        municipalities = gpd.read_file(os.path.join(static_folder, "test_vigi_bf_com.shp"))

        second_col_name = ffft_df.columns[1]
        ffft_df = ffft_df.rename(columns={second_col_name: "FFFT"})
        date_str, hour_str = second_col_name[7:15], second_col_name[15:17]

        ffft_df["FFFT"] = pd.to_numeric(ffft_df["FFFT"], errors="coerce")
        ffft_df["FFFT"] = ffft_df["FFFT"].replace(-999.00, np.nan)

        merged = coverage.merge(ffft_df, left_on="value", right_on="BASIN", how="left")
        merged["na_rm_percentage"] = merged["percent_coverage"] * merged["FFFT"].notna()
        merged["weighted_FFFT"] = merged["percent_coverage"] * merged["FFFT"]

        weighted_sum = merged.groupby("ADM3_FR", as_index=False)["weighted_FFFT"].sum()
        weighted_percentage = merged.groupby("ADM3_FR", as_index=False)["na_rm_percentage"].sum()

        weighted_sum["weighted_FFFT"] = weighted_sum["weighted_FFFT"] / weighted_percentage["na_rm_percentage"]
        municipalities = municipalities.merge(weighted_sum, on="ADM3_FR", how="left")
        municipalities["weighted_FFFT"] = municipalities["weighted_FFFT"].fillna(0)
        municipalities["weighted_FFFT"] = municipalities["weighted_FFFT"].round(2)
        municipalities["vigilance"] = municipalities["weighted_FFFT"].apply(assign_vigilance)

        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        formatted_hour = f"{int(hour_str):02d}"
        timestamp_label = f"{formatted_date}-{formatted_hour}"

        level_warnings = municipalities[["ADM3_FR", "vigilance", "weighted_FFFT"]].rename(
            columns={"vigilance": timestamp_label}
        )
        level_warnings.insert(0, "SUBID", range(1, len(level_warnings) + 1))
        level_warnings.insert(0, "index", range(1, len(level_warnings) + 1))
        return level_warnings
    except Exception as e:
        logging.error(f"[WAFFGS][INGEST] - Error processing file {file_path}: {e}")
        raise


def  ingest_ffgs_data(file_path: str):

    logging.info(f"[WAFFGS][INGEST] - Start for file {os.path.basename(file_path)}")
    level_warnings = extract_ffgs_from_source(file_path)
    logging.info(f"[WAFFGS][INGEST] - Extraction done.")
    flash_floods = []
    date_cols = get_dates_from_dataframe(level_warnings)
    init_date = date_cols[0]

    for _, row in level_warnings.iterrows():
        fid = int(row["index"])
        subid = row["SUBID"]
        adm3_fr = row["ADM3_FR"]
        weighted_ffft = row["weighted_FFFT"]
        forecast_date = pd.to_datetime(init_date)
        value = int(row[init_date])

        ff_db = FlashFlood.query.filter_by(forecast_date=forecast_date,
                                                 fid=fid).first()
        if ff_db is not None:
            continue

        rf = FlashFlood(
            fid=fid,
            subid=subid,
            adm3_fr=adm3_fr,
            forecast_date=forecast_date,
            init_value=value,
            value=value,
            weighted_ffft=weighted_ffft
        )
        flash_floods.append(rf)

    logging.info("[WAFFGS][INGEST] - Ingest in base")
    for db_flash_flood in flash_floods:
        db.session.add(db_flash_flood)

    db.session.flush(flash_floods)
    db.session.commit()
    logging.info("[WAFFGS][INGEST] - Success")

    return flash_floods

