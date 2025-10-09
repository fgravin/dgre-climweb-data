import logging
import os

import pandas as pd
from sqlalchemy import desc

from dgrehydro import SETTINGS
from dgrehydro.ingestors.hype.hype_fetch import HYPE_FOLDER
from dgrehydro.ingestors.hype.hype_io import read_time_output
from dgrehydro.models._geo_riversegment import RiverSegment
from dgrehydro.models.riverineflood import RiverineFlood


def wldef(subid, thisq1, retlev2, wl_rp):
    """Determine warning level for one subbasin."""
    myf = thisq1[subid].astype(float)
    mywl = 0
    if not retlev2[subid].isna().all():
        for k, rp in enumerate(wl_rp):
            if any(myf > retlev2.loc[f"RP{rp}", subid]):
                mywl = k + 1
    return mywl

def process_hype_data(model: str, date_str: str) -> bool:
    root_data_dir = os.path.join(SETTINGS.get('DATA_DIR'), HYPE_FOLDER)
    data_dir = os.path.join(root_data_dir, model, date_str)
    static_dir =  os.path.join(SETTINGS.get('DATA_DIR'), 'static', HYPE_FOLDER)

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
    forecast_data.to_csv(os.path.join(data_dir, "hindcast.csv"), index=False)

    # 3. Prepare colorscales
    retlev = pd.read_csv(threshold_file, delim_whitespace=True)
    retlev2 = retlev.set_index("SUBID").T
    wl_rp = [int(x.replace("RP", "")) for x in retlev2.index]

    # Read current forecast again
    thisq = read_time_output(os.path.join(data_dir, forecast_file))
    all_date = thisq.iloc[:, 0].astype(str).values
    thisq.columns = [c.replace("X", "") for c in thisq.columns]
    thisq = thisq.drop(thisq.columns[0], axis=1)

    mmymatch = [c for c in thisq.columns if c in retlev2.columns]
    retlev2 = retlev2[mmymatch]

    if list(thisq.columns) == list(retlev2.columns):
        all_wls = []
        for _, row in thisq.iterrows():
            thisq1 = pd.DataFrame([row])
            wl_levels = {subid: wldef(subid, thisq1, retlev2, wl_rp) for subid in thisq1.columns}
            all_wls.append(list(wl_levels.values()))

        thiswl_df = pd.DataFrame(all_wls, columns=thisq.columns)
        thiswl_df.insert(0, "SUBID", range(1, len(thiswl_df) + 1))
        thiswl_df["WarningLevel_max"] = thiswl_df.max(axis=1, skipna=True)
        out_file = os.path.join(data_dir, f"004_mapWarningLevel_{date_str}.txt")

        with open(out_file, "w") as f:
            f.write(f" Warning levels based on magnitudes with return-period: {', '.join(map(str, wl_rp))} years\n")
        thiswl_df.to_csv(out_file, mode="a", index=False)

        # Write colorscales
        thiswl_df2 = thiswl_df.copy()
        thiswl_df2.insert(0, "index", range(1, len(thiswl_df2) + 1))
        # thiswl_df2.to_csv(os.path.join(wl_dir, "colorscales.csv"), index=False)
        # thiswl_df2.to_csv(os.path.join(wl_dir, "colorscales1.csv"), index=False)

        # Forecast dates
        forecast_date = pd.DataFrame({
            "Jour": [f"day{i+1}" for i in range(10)] + ["max"],
            "Date": list(all_date[:10]) + ["Max of 10 days forecast"]
        })

        riverine_floods = []
        for _, row in thiswl_df2.iterrows():
            fid = int(row["index"])
            subid = str(row["SUBID"])

            db_river_segment = RiverSegment.query.get(subid)
            if db_river_segment is None:
                continue

            for date in list(all_date[:10]):
                forecast_date = pd.to_datetime(date)
                value = int(row[date])
                rf = RiverineFlood(
                    fid=fid,
                    subid=subid,
                    init_date=date_str,
                    forecast_date=forecast_date,
                    init_value=value,
                    value=value
                )
                riverine_floods.append(rf)
        return riverine_floods

        forecast_date.to_csv(os.path.join(wl_dir, "forecast_dates.csv"), index=False)

