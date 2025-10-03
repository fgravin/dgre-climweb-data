import logging
from datetime import datetime, timedelta

import pytz

from dgrehydro import db
from dgrehydro.config.country_config import country_config
from dgrehydro.models.dustwarning import DustWarning
from dgrehydro.utils import get_json_warnings


def load_warnings():

    day_vals = ["0", "1", "2"]

    next_update = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    target_timezone = pytz.timezone('Europe/Paris')
    current_time_utc_plus_one = datetime.now(target_timezone)

    # only run after 12:05 UTC+1
    # This is the time when the AEMET data is likely to have been updated
    if current_time_utc_plus_one < current_time_utc_plus_one.replace(hour=12, minute=5):
        logging.warning(f"[WARNINGS]: Skipping warnings update as it is before 12:05 UTC+1. "
                        f"Current time is {current_time_utc_plus_one}")
        return None

    if next_update:
        next_update_str = next_update.strftime("%Y%m%d")
        next_update_str_iso = next_update.isoformat()

        config = country_config.get('BFA')
        country_iso = config.get("iso")

        logging.info("[INGESTION][DUST_WARNINGS]: Loading warnings for {}".format('BFA'))

        id_field = config.get("id_field")
        name_field = config.get("name_field")

        geojson_url_template = config.get("geojson_url_template")

        warnings_data = {}

        for day_val in day_vals:
            forecast_date = next_update + timedelta(days=int(day_val))

            geojson_url = geojson_url_template.format(date_str=next_update_str, day_val=day_val)

            logging.info(f"[INGESTION][DUST_WARNINGS]: Fetching warnings for date {next_update_str} and day {day_val}")

            try:
                geojson_warnings = get_json_warnings(geojson_url)

                if not geojson_warnings:
                    logging.warning(f"[INGESTION][DUST_WARNINGS]: No warnings found for {geojson_url}")
                    return False

                if geojson_warnings:
                    features = geojson_warnings.get("features")

                    if not features:
                        logging.warning(f"[INGESTION][DUST_WARNINGS]: No features found for {geojson_url}")
                        return False

                    for feature in features:
                        props = feature.get("properties")

                        id_prop = props.get(id_field)
                        name = props.get(name_field)

                        if id_prop is None and name is None:
                            logging.info(f"[DUST_WARNINGS]: Skipping ")
                            return False

                        gid = f"{country_iso}_{id_prop}"
                        value = props["value"]

                        d_data = {
                            "gid": gid,
                            "init_date": next_update,
                            "forecast_date": forecast_date,
                            "value": value
                        }

                        if not warnings_data.get(gid):
                            warnings_data[gid] = [d_data]
                        else:
                            warnings_data[gid].append(d_data)

            except Exception as e:
                logging.info(f"[INGESTION][DUST_WARNINGS]: {e}")
                return False

        for gid, warning_items in warnings_data.items():
            for warning_data in warning_items:
                exists = False
                db_warning = DustWarning.query.filter_by(init_date=warning_data.get("init_date"),
                                                         forecast_date=warning_data.get("forecast_date"),
                                                         gid=gid).first()
                if db_warning:
                    exists = True
                else:
                    db_warning = DustWarning(**warning_data)

                if exists:
                    logging.info('[DUST_WARNINGS]: UPDATE')
                    db_warning.value = warning_data["value"]
                else:
                    logging.info('[DUST_WARNINGS]: ADD')
                    db.session.add(db_warning)
                db.session.commit()

        logging.info(f"[INGESTION][DUST_WARNINGS]: Done fetching warnings for date {next_update_str}")
        return None
    return None
