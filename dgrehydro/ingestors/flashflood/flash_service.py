import logging
from datetime import datetime, timedelta

from dgrehydro.ingestors.flashflood.flash_fetch import fetch_waffgs_data
from dgrehydro.ingestors.flashflood.flash_ingest import ingest_ffgs_data
from dgrehydro.models.flashflood import FlashFlood


def ingest_flashfloods(date: str, since: str):
    logging.info("[INGESTION][FLASHFLOOD]: Start")
    if date is None:
        logging.info("[INGESTION][FLASHFLOOD]: Ingest last data")
        ingest_last_flashflood_data()
    else:
        if since is None:
            logging.info("[INGESTION][FLASHFLOOD]: Ingest day %s", date)
            ingest_flashflood_for_date(date)
        else:
            logging.info("[INGESTION][FLASHFLOOD]: Ingest all days since %s", date)
            ingest_flashfloods_since(date)
    logging.info("[INGESTION][FLASHFLOOD]: Success")


def ingest_flashfloods_since(date: str):
    logging.info("[INGESTION][DUST_WARNINGS]: Start")
    required_date = datetime.strptime(date, "%Y%m%d")
    current_date = datetime.utcnow()
    while required_date <= current_date:
        ingest_flashflood_for_date(required_date.strftime("%Y%m%d"))
        required_date = required_date.replace(hour=0) + timedelta(days=1)


def ingest_last_flashflood_data() -> list[FlashFlood]:
    filename = fetch_waffgs_data()
    return ingest_ffgs_data(filename)


def ingest_flashflood_for_date(date: str):
    required_date = datetime.strptime(date, "%Y%m%d")
    utc_hours = [2, 8, 14, 20]
    results = []
    for hour in utc_hours:
        dt = required_date.replace(hour=hour)
        filename = fetch_waffgs_data(dt)
        floods = ingest_ffgs_data(filename)
        results.extend(floods)
    return results
