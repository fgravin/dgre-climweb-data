import logging
import os
import re

import pandas as pd
import numpy as np

from dgrehydro import SETTINGS
from dgrehydro.ingestors.hype.hype_fetch import HYPE_FOLDER
from dgrehydro.ingestors.hype.hype_io import read_time_output
from dgrehydro.models._geo_riversegment import RiverSegment
from dgrehydro.models.riverineflood import RiverineFlood


def wldef(subid, thisq1, retlev2, wl_rp):
    """Determine warning level for one subbasin."""
    myf = float(thisq1[subid])
    mywl = 0
    if subid in retlev2.columns and not retlev2[subid].isna().all():
        for k, rp in enumerate(wl_rp):
            threshold = retlev2.loc[f"RP{rp}", subid]
            if pd.notna(threshold) and myf > threshold:
                mywl = k + 1
    return mywl

def process_hype_data(model: str, date_str: str) -> bool:
    root_data_dir = os.path.join(SETTINGS.get('DATA_DIR'), HYPE_FOLDER)
    data_dir = os.path.join(root_data_dir, model, date_str)
    static_dir = os.path.abspath(os.path.join(SETTINGS.get('STATIC_DATA_DIR'), "hype"))

    if not os.path.exists(data_dir):
        logging.warn(f"[HYPE][PROCESS] Data have not been downloaded yet for date {date_str}.")
        return False

    # latest_init_date = RiverineFlood.query.order_by(desc(RiverineFlood.init_date)).first()
    # if latest_init_date < date_str:
    #     logging.warn(f"[HYPE][PROCESS] Data have already been processed for date {date_str}.")
    #     return False

    threshold_file = os.path.join(static_dir, 'riverine', "thresholds-rp-cout.txt")

    all_files = os.listdir(data_dir)
    forecast_file = next(f for f in all_files if "forecast_timeCOUT" in f)
    hindcast_file = next(f for f in all_files if "hindcast_timeCOUT" in f)

    # Read forecast
    forecast_data = read_time_output(os.path.join(data_dir, forecast_file))
    forecast_data = forecast_data.T
    forecast_data.columns = forecast_data.iloc[0]
    forecast_data = forecast_data.drop(forecast_data.index[0])
    forecast_data.insert(0, "SUBID", forecast_data.index.str.replace("X", ""))
    forecast_data.insert(0, "index", range(1, len(forecast_data) + 1))
    forecast_data.to_csv(os.path.join(data_dir, "forecast.csv"), index=False)

    # Read hindcast
    hindcast_data = read_time_output(os.path.join(data_dir, hindcast_file))
    hindcast_data = hindcast_data.T
    hindcast_data.columns = hindcast_data.iloc[0]
    hindcast_data = hindcast_data.drop(hindcast_data.index[0])
    hindcast_data.insert(0, "SUBID", hindcast_data.index.str.replace("X", ""))
    hindcast_data.insert(0, "index", range(1, len(hindcast_data) + 1))
    hindcast_data.to_csv(os.path.join(data_dir, "hindcast.csv"), index=False)

    # 3. Prepare colorscales
    # Read return level thresholds
    retlev = pd.read_csv(threshold_file, sep='\s+')
    retlev2 = retlev.drop(columns=["SUBID"]).T
    retlev2.columns = retlev["SUBID"].astype(str)

    # Extract return periods from row names (e.g., "RP2" -> 2)
    wl_rp = [int(rp.replace("RP", "")) for rp in retlev2.index]

    # Read forecast discharge data for warning level calculation
    thisq = read_time_output(os.path.join(data_dir, forecast_file))

    # Store dates
    all_dates = thisq["DATE"]

    # Remove DATE column and clean column names
    thisq = thisq.drop(columns=["DATE"])
    thisq.columns = thisq.columns.str.replace("X", "")

    common_cols = [col for col in thisq.columns if col in retlev2.columns]
    retlev2 = retlev2[common_cols]
    thisq = thisq[common_cols]

    # Check that columns match
    if list(thisq.columns) != list(retlev2.columns):
        print("Warning: Column mismatch between forecast and return levels!")
        print(f"Forecast columns: {len(thisq.columns)}")
        print(f"Return level columns: {len(retlev2.columns)}")
        # Try to align them
        common_cols = [col for col in thisq.columns if col in retlev2.columns]
        if common_cols:
            thisq = thisq[common_cols]
            retlev2 = retlev2[common_cols]
        else:
            print("No common columns found. Skipping.")
            return

    # Calculate warning levels for each day
    thiswls = []
    for day_idx in range(len(thisq)):
        thisq1 = thisq.iloc[day_idx]
        thiswl = []
        for subid in thisq.columns:
            wl_val = wldef(subid, thisq1, retlev2, wl_rp)
            thiswl.append(wl_val)
        thiswls.append(thiswl)

    # Convert to DataFrame
    thiswls_array = np.array(thiswls).T

    # Calculate max warning level across all days
    max_wl = np.max(thiswls_array, axis=1)

    # Create warning level DataFrame
    thiswl_df = pd.DataFrame(thiswls_array, columns=[str(d) for d in all_dates])
    thiswl_df.insert(0, "SUBID", [int(sid) for sid in thisq.columns])
    thiswl_df["WarningLevel_max"] = max_wl

    # Save warning level file with header
    wl_file = os.path.join(data_dir, f"004_mapWarningLevel_{date_str}.txt")
    with open(wl_file, "w") as f:
        f.write(f" Warning levels based on magnitudes with return-period: {', '.join(map(str, wl_rp))} years\n")
    thiswl_df.to_csv(wl_file, index=False, mode="a")
    print(f"Saved warning levels to: {wl_file}")

    # Create colorscales file (for Tethys)
    colorscales_df = thiswl_df.copy()
    colorscales_df.insert(0, "index", range(1, len(colorscales_df) + 1))
    colorscales_df.columns = ["index", "SUBID"] + [f"day{i+1}" for i in range(len(all_dates))] + ["max"]

    # Create forecast dates file
    forecast_dates_df = pd.DataFrame({
        "Jour": [f"day{i+1}" for i in range(len(all_dates))] + ["max"],
        "Date": [str(d)[:10] for d in all_dates] + ["Max of 10 days forecast"]
    })

    riverine_floods = []

    day_cols = [col for col in colorscales_df.columns if re.match(r'^day\d+$', col)]
    day_date_map = map_day_date(forecast_dates_df)
    init_date = pd.to_datetime(day_date_map[day_cols[0]])

    for _, row in colorscales_df.iterrows():
        fid = int(row["index"])
        subid = str(row["SUBID"])

        db_river_segment = RiverSegment.query.get(subid)
        if db_river_segment is None:
            logging.warn(f"[HYPE][PROCESS] SubID {subid} not found in RiverSegment table. Skipping.")
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
