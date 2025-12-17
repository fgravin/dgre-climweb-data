import logging
import os
import re
from datetime import datetime, timedelta

import pandas as pd

from dgrehydro import SETTINGS, db
from dgrehydro.models.poiflow import PoiFlow


def ingest_poi_flow_from_csv() -> list[PoiFlow]:
    """
    Main ingestion function for POI flow data.
    Ingests real-time flow measurements and forecasts for 6 POI stations.
    """
    data_dir = SETTINGS['DATA_POI_FLOW_SOURCE_DIR']
    csv_path = find_latest_poi_flow_csv(data_dir)

    logging.info(f"[INGESTION][POI_FLOW][CSV] Load {csv_path}")
    if not os.path.exists(csv_path):
        logging.error(f"[INGESTION][POI_FLOW][CSV] CSV file {csv_path} does not exist.")
        raise FileNotFoundError(f"CSV file {csv_path} does not exist.")

    db_poi_flows = extract_db_poi_flows_from_csv(csv_path)

    logging.info(f"[INGESTION][POI_FLOW][CSV]: Ingest {len(db_poi_flows)} records in database")
    for db_poi_flow in db_poi_flows:
        db.session.add(db_poi_flow)

    db.session.flush(db_poi_flows)
    db.session.commit()
    logging.info("[INGESTION][POI_FLOW][CSV]: Done")
    return db_poi_flows


def find_latest_poi_flow_csv(data_dir: str) -> str:
    """
    Find the most recent POI flow CSV file in the data directory.
    Expected filename pattern: SAPCI_LOCAL_POIS{YYYY-MM-DD-HH-MM}.csv
    """
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory {data_dir} does not exist.")

    files = [f for f in os.listdir(data_dir) if f.startswith("SAPCI_LOCAL_POIS") and f.endswith(".csv")]

    if not files:
        raise FileNotFoundError(f"No POI flow CSV files found in {data_dir}")

    date_files = []
    for f in files:
        # Pattern: SAPCI_LOCAL_POIS2025-10-31-13-27.csv
        m = re.search(r"SAPCI_LOCAL_POIS(\d{4}-\d{2}-\d{2}-\d{2}-\d{2})", f)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d-%H-%M")
                date_files.append((dt, f))
            except ValueError:
                logging.warning(f"[INGESTION][POI_FLOW][CSV] Could not parse date from filename: {f}")
                continue

    if not date_files:
        raise FileNotFoundError(f"No valid POI flow CSV files with date pattern found in {data_dir}")

    latest_file = max(date_files, key=lambda x: x[0])[1]
    logging.info(f"[INGESTION][POI_FLOW][CSV] Found latest file: {latest_file}")
    return os.path.join(data_dir, latest_file)


def extract_db_poi_flows_from_csv(csv_path: str) -> list[PoiFlow]:
    """
    Parse POI flow CSV and create database objects.

    CSV Structure:
    - Column 1: Date (DD/MM/YYYY HH:MM:SS)
    - Column 2: Offset (in minutes, 0=real-time, 1440=+1day, etc.)
    - Remaining columns: pairs of {Station} - Débit - Débit and {Station} - Radar - limni

    Stations: Dan, Diarabakoko, Gampela, Heredougou, Nobere, Rakaye
    """
    # Read CSV with semicolon separator and comma as decimal
    df = pd.read_csv(csv_path, sep=';', decimal=',')

    # Clean column names (remove BOM and extra spaces)
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')

    poi_flows = []

    # Parse station columns (every pair of columns after Date and Offset)
    stations = extract_station_names(df.columns)

    logging.info(f"[INGESTION][POI_FLOW][CSV] Found {len(stations)} stations: {stations}")

    for _, row in df.iterrows():
        try:
            # Parse measurement date
            measurement_date = pd.to_datetime(row['Date'], format='%d/%m/%Y %H:%M:%S')
            offset = int(row['Offset'])

            # Calculate forecast date
            forecast_date = measurement_date + timedelta(minutes=offset)

            # Extract data for each station
            for station_name in stations:
                flow_col = f"{station_name} - Débit - Débit"
                limni_col = f"{station_name} - Radar - limni"

                # Get values, handle missing data
                flow = float(row[flow_col]) if pd.notna(row[flow_col]) else None
                water_level = float(row[limni_col]) if pd.notna(row[limni_col]) else None

                poi_flow = PoiFlow(
                    station_name=station_name,
                    measurement_date=measurement_date,
                    forecast_date=forecast_date,
                    flow=flow,
                    water_level=water_level
                )
                poi_flows.append(poi_flow)

        except Exception as e:
            logging.error(f"[INGESTION][POI_FLOW][CSV] Error processing row: {e}")
            continue

    logging.info(f"[INGESTION][POI_FLOW][CSV] Extracted {len(poi_flows)} POI flow records")
    return poi_flows


def extract_station_names(columns) -> list[str]:
    """
    Extract unique station names from CSV columns.
    Expected pattern: {Station} - Débit - Débit or {Station} - Radar - limni
    """
    stations = set()
    for col in columns:
        if col in ['Date', 'Offset']:
            continue
        # Extract station name (everything before the first " - ")
        parts = col.split(' - ')
        if len(parts) >= 2:
            station_name = parts[0].strip()
            stations.add(station_name)

    return sorted(list(stations))
