import logging
from datetime import timedelta

import pandas as pd

from dgrehydro import SETTINGS
from dgrehydro.models.criticalpoint import CriticalPoint

# Load water level thresholds from static data
_thresholds = None


def load_thresholds() -> dict:
    """
    Load water level thresholds from CSV file.
    Returns a dict: {station_name: {'green_yellow': x, 'yellow_orange': y, 'orange_red': z}}
    """
    global _thresholds
    if _thresholds is not None:
        return _thresholds

    thresholds_file = SETTINGS.get('CRITICAL_POINT_THRESHOLDS_FILE')
    logging.info("[CRITPOINT][INGEST]: Loading thresholds from %s", thresholds_file)

    df = pd.read_csv(thresholds_file, sep=';', decimal=',')
    df.columns = df.columns.str.strip()

    _thresholds = {}
    for _, row in df.iterrows():
        station = row['Site'].strip()
        _thresholds[station] = {
            'green_yellow': float(row['vert-jaune']),
            'yellow_orange': float(row['jaune-orange']),
            'orange_red': float(row['orange-rouge'])
        }

    logging.info("[CRITPOINT][INGEST]: Loaded thresholds for %d stations", len(_thresholds))
    return _thresholds


def compute_water_level_alert(station_name: str, water_level: float) -> int:
    """
    Compute water level alert based on thresholds.

    Alert levels:
    - 1: Green (water_level <= green_yellow threshold)
    - 2: Yellow (green_yellow < water_level <= yellow_orange)
    - 3: Orange (yellow_orange < water_level <= orange_red)
    - 4: Red (water_level > orange_red)

    Args:
        station_name: Name of the station
        water_level: Water level value

    Returns:
        Alert level (1-4) or None if water_level is None or station not found
    """
    if water_level is None:
        return None

    thresholds = load_thresholds()
    if station_name not in thresholds:
        logging.warning("[CRITPOINT][INGEST]: No thresholds found for station %s", station_name)
        return None

    station_thresholds = thresholds[station_name]

    if water_level <= station_thresholds['green_yellow']:
        return 1  # Green
    elif water_level <= station_thresholds['yellow_orange']:
        return 2  # Yellow
    elif water_level <= station_thresholds['orange_red']:
        return 3  # Orange
    else:
        return 4  # Red


def extract_db_critical_points_from_csv(csv_path: str) -> list[CriticalPoint]:
    """
    Parse critical point CSV and create database objects.

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

                # Compute water level alert
                water_level_alert = compute_water_level_alert(station_name, water_level)

                critical_point = CriticalPoint(
                    station_name=station_name,
                    measurement_date=measurement_date,
                    forecast_date=forecast_date,
                    flow=flow,
                    water_level=water_level,
                    water_level_alert=water_level_alert
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
