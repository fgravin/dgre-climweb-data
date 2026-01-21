import logging
from datetime import timedelta

import pandas as pd

from dgrehydro.models.criticalpoint import CriticalPoint


def extract_db_critical_points_from_csv(csv_path: str) -> list[CriticalPoint]:
    """
    Parse POI flow CSV and create database objects.

    CSV Structure:
    - Column 1: Date (DD/MM/YYYY HH:MM:SS)
    - Column 2: Offset (in minutes, 0=real-time, 1440=+1day, etc.)
    - Remaining columns: pairs of {Station} - Débit - Débit and {Station} - Radar - limni

    Args:
        csv_path: Path to the CSV file to process

    Returns:
        List of CriticalPoint database objects
    """
    logging.info("[CRITPOINT][INGEST]: Processing CSV %s", csv_path)

    # Read CSV with semicolon separator and comma as decimal
    df = pd.read_csv(csv_path, sep=';', decimal=',')

    # Clean column names (remove BOM and extra spaces)
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')

    critical_points = []

    # Parse station columns (every pair of columns after Date and Offset)
    stations = extract_station_names(df.columns)

    logging.info("[CRITPOINT][INGEST]: Found %d stations: %s", len(stations), stations)

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
                flow = None
                water_level = None

                if flow_col in df.columns:
                    flow = float(row[flow_col]) if pd.notna(row[flow_col]) else None
                if limni_col in df.columns:
                    water_level = float(row[limni_col]) if pd.notna(row[limni_col]) else None

                critical_point = CriticalPoint(
                    station_name=station_name,
                    measurement_date=measurement_date,
                    forecast_date=forecast_date,
                    flow=flow,
                    water_level=water_level
                )
                critical_points.append(critical_point)

        except Exception as e:
            logging.error("[CRITPOINT][INGEST]: Error processing row: %s", str(e))
            continue

    logging.info("[CRITPOINT][INGEST]: Extracted %d critical point records", len(critical_points))
    return critical_points


def extract_station_names(columns) -> list[str]:
    """
    Extract unique station names from CSV columns.
    Expected pattern: {Station} - Débit - Débit or {Station} - Radar - limni

    Args:
        columns: DataFrame columns

    Returns:
        Sorted list of unique station names
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
