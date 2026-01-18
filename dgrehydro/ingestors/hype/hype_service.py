import logging
from datetime import datetime, timedelta
from dgrehydro import db

from dgrehydro.ingestors.hype.hype_fetch import fetch_daily_hype_data
from dgrehydro.ingestors.hype.process_hype import process_hype_data


def ingest_hype_data(date: str, since: str):
    logging.info("[INGESTION][HYPE]: Start")
    if date is None:
        logging.info("[INGESTION][HYPE]: Ingest last data")
        ingest_last_hype_data()
    else:
        if since is None:
            logging.info("[INGESTION][HYPE]: Ingest day %s", date)
            ingest_hype_for_date(date)
        else:
            logging.info("[INGESTION][HYPE]: Ingest all days since %s", date)
            ingest_hype_since(date)
    logging.info("[INGESTION][HYPE]: Success")


def ingest_hype_since(date: str):
    logging.info("[INGESTION][HYPE]: Start since %s", date)
    required_date = datetime.strptime(date, "%Y%m%d")
    current_date = datetime.utcnow()
    while required_date <= current_date:
        ingest_hype_for_date(required_date.strftime("%Y%m%d"))
        required_date = required_date.replace(hour=0) + timedelta(days=1)


def ingest_last_hype_data():
    """Fetch and process the latest HYPE data."""
    utc_time = datetime.utcnow()
    fetch_daily_hype_data(utc_time)
    date_str = utc_time.strftime("%Y%m%d")
    ingest_hype_for_date(date_str)


def ingest_hype_for_date(date: str):
    """Fetch and process HYPE data for a specific date."""
    required_date = datetime.strptime(date, "%Y%m%d")
    logging.info("[INGESTION][HYPE]: Fetching data for %s", required_date.strftime("%Y-%m-%d"))

    # Fetch data from FTP
    try:
        fetch_daily_hype_data(required_date)
    except Exception as e:
        logging.error("[INGESTION][HYPE]: Failed to fetch data for %s: %s", date, str(e))
        return None

    # Process only Burkina Faso model
    model_path = "bf-hype1.0_chirps2.0_gefs_noEOWL_noINSITU"
    logging.info("[INGESTION][HYPE]: Processing model %s for date %s", model_path, date)
    try:
        db_riverine_floods = process_hype_data(model_path, date)
        logging.info("[INGESTION][HYPE]: Ingest in base")
        for db_riverine_flood in db_riverine_floods:
            db.session.add(db_riverine_flood)

        db.session.flush(db_riverine_floods)
        db.session.commit()

    except Exception as e:
        logging.error("[INGESTION][HYPE]: Failed to process model %s: %s", model_path, str(e))
        return None
