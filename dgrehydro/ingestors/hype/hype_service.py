import logging
from datetime import datetime, timedelta

from dgrehydro import db
from dgrehydro.ingestors.hype.hype_fetch import fetch_daily_hype_data, HYPE_MODELS
from dgrehydro.ingestors.hype.process_hype import process_hype_data
from dgrehydro.models.riverineflood import RiverineFlood


def ingest_riverinefloods(date: str = None, since: str = None, model: str = None):
    logging.info("[INGESTION][HYPE]: Start")

    if date is None:
        logging.info("[INGESTION][HYPE]: Ingest latest data")
        ingest_hype_for_date(model)
    else:
        if since is None:
            logging.info("[INGESTION][HYPE]: Ingest date %s", date)
            today = datetime.now().strftime("%Y%m%d")
            ingest_hype_for_date(today, model)
        else:
            logging.info("[INGESTION][HYPE]: Ingest all dates since %s", since)
            ingest_riverinefloods_since(since, model)

    logging.info("[INGESTION][HYPE]: Success")


def ingest_riverinefloods_since(start_date: str, model: str = None):
    logging.info("[INGESTION][HYPE]: Bulk ingestion from %s", start_date)

    required_date = datetime.strptime(start_date, "%Y%m%d")
    current_date = datetime.utcnow()

    while required_date <= current_date:
        date_str = required_date.strftime("%Y%m%d")
        try:
            ingest_hype_for_date(date_str, model)
        except Exception as e:
            logging.error(f"[INGESTION][HYPE]: Error ingesting date {date_str}: {e}")
        required_date = required_date + timedelta(days=1)


def ingest_hype_for_date(date_str: str, model: str = None) -> list[RiverineFlood]:
    logging.info(f"[INGESTION][HYPE]: Processing data for date {date_str}")

    all_results = []

    success = fetch_daily_hype_data(date_str)
    if not success:
        logging.error("[INGESTION][HYPE]: Failed to fetch data")
        return []

    # Determine which models to process
    models_to_process = HYPE_MODELS
    if model:
        models_to_process = [m for m in HYPE_MODELS if m['path'] == model]
        if not models_to_process:
            logging.error(f"[INGESTION][HYPE]: Model {model} not found")
            return []

    # Process each model
    for hype_model in models_to_process:
        model_name = hype_model['name']
        model_path = hype_model['path']

        logging.info(f"[INGESTION][HYPE]: Processing model {model_name}")

        try:
            # Process HYPE data and get RiverineFlood records
            riverine_floods = process_hype_data(model_path, date_str)

            if riverine_floods:
                # Persist to database
                logging.info(f"[INGESTION][HYPE]: Inserting {len(riverine_floods)} records from {model_name}")

                for flood in riverine_floods:
                    db.session.add(flood)

                db.session.commit()
                all_results.extend(riverine_floods)

                logging.info(f"[INGESTION][HYPE]: Successfully ingested {len(riverine_floods)} records from {model_name}")
            else:
                logging.warning(f"[INGESTION][HYPE]: No data generated for {model_name} on {date_str}")

        except Exception as e:
            logging.error(f"[INGESTION][HYPE]: Error processing {model_name}: {e}")
            db.session.rollback()
            continue

    logging.info(f"[INGESTION][HYPE]: Total records ingested: {len(all_results)}")
    return all_results


def get_available_models() -> list[dict]:
    """
    Get list of available HYPE models.

    Returns:
        List of model dictionaries with name and path
    """
    return HYPE_MODELS


def ingest_hype_model(model_name: str, date_str: str = None) -> list[RiverineFlood]:
    """
    Ingest data for a specific HYPE model.

    Args:
        model_name: Name of the model (from HYPE_MODELS)
        date_str: Date in YYYYMMDD format, or None for today

    Returns:
        List of created RiverineFlood records
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    # Find model by name
    model = next((m for m in HYPE_MODELS if m['name'] == model_name), None)

    if not model:
        logging.error(f"[INGESTION][HYPE]: Model '{model_name}' not found")
        return []

    return ingest_hype_for_date(date_str, model['path'])
