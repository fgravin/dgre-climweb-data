import logging
from datetime import datetime, timedelta

from dgrehydro import db
from dgrehydro.ingestors.critical_points.critpoint_fetch import fetch_critpoint_data
from dgrehydro.ingestors.critical_points.critpoint_ingest import extract_db_critical_points_from_csv


def ingest_critpoint_data(date: str, since: str):
    """
    Main entry point for critical points ingestion.

    Args:
        date: Date in YYYYMMDD format, or None for today
        since: If provided (any value), ingest from date to current UTC time
    """
    logging.info("[INGESTION][CRITPOINT]: Start")
    if date is None:
        logging.info("[INGESTION][CRITPOINT]: Ingest last data")
        ingest_last_critpoint_data()
    else:
        if since is None:
            logging.info("[INGESTION][CRITPOINT]: Ingest day %s", date)
            ingest_critpoint_for_date(date)
        else:
            logging.info("[INGESTION][CRITPOINT]: Ingest all days since %s", date)
            ingest_critpoint_since(date)
    logging.info("[INGESTION][CRITPOINT]: Success")


def ingest_critpoint_since(date: str):
    """
    Ingest critical points data for all dates from given date to current UTC time.

    Args:
        date: Start date in YYYYMMDD format
    """
    logging.info("[INGESTION][CRITPOINT]: Start since %s", date)
    required_date = datetime.strptime(date, "%Y%m%d")
    current_date = datetime.utcnow()
    while required_date <= current_date:
        ingest_critpoint_for_date(required_date.strftime("%Y%m%d"))
        required_date = required_date.replace(hour=0) + timedelta(days=1)


def ingest_last_critpoint_data():
    """Fetch and process the latest critical points data."""
    utc_time = datetime.utcnow()
    date_str = utc_time.strftime("%Y%m%d")
    ingest_critpoint_for_date(date_str)


def ingest_critpoint_for_date(date: str):
    """
    Fetch and process critical points data for a specific date.

    Args:
        date: Date in YYYYMMDD format
    """
    required_date = datetime.strptime(date, "%Y%m%d")
    logging.info("[INGESTION][CRITPOINT]: Fetching data for %s", required_date.strftime("%Y-%m-%d"))

    # Fetch data from FTP
    try:
        csv_path = fetch_critpoint_data(required_date)
    except Exception as e:
        logging.error("[INGESTION][CRITPOINT]: Failed to fetch data for %s: %s", date, str(e))
        return None

    if csv_path is None:
        logging.warning("[INGESTION][CRITPOINT]: No data available for %s", date)
        return None

    # Process CSV and ingest into database
    logging.info("[INGESTION][CRITPOINT]: Processing CSV for date %s", date)
    try:
        db_critical_points = extract_db_critical_points_from_csv(csv_path)
        logging.info("[INGESTION][CRITPOINT]: Ingest %d records in database", len(db_critical_points))

        for db_critical_point in db_critical_points:
            db.session.add(db_critical_point)

        db.session.flush(db_critical_points)
        db.session.commit()
        logging.info("[INGESTION][CRITPOINT]: Done for date %s", date)

    except Exception as e:
        logging.error("[INGESTION][CRITPOINT]: Failed to process data for %s: %s", date, str(e))
        return None
