# DGRE Hydro

This is a web application for managing and visualizing hydrological data, for DGRE in Burkina Faso. It provides
functionalities to ingest, update, and visualize flood data.

## Get started

Copy `.env.sample` to `.env` and fill in the required values.

```bash
docker compose --profile production build
docker compose --profile production up
```

This will start a 
- PostgreSQL database with PostGIS extension,
- A Nginx server to reverse proxy requests on `http://localhost:${APP_PORT}/`
- PGTileServ to serve map tiles on `http://localhost:${APP_PORT}/pgtileserv/`,
- A Flask CLI to manage database and ingestion tasks, and
- A Flask web application to provide API endpoints EG. `http://localhost:${APP_PORT}/api/v1/riverineflood`

## Development mode
### Setup the environment
Copy `.env.sample` to `.env` and fill in the required values.
```bash
python3.11 -m venv .venv
poetry install
source .venv/bin/activate
```

### Run DB and PGTileServ as docker containers

This will open `55432` (postgres) & `7800` (pg_tilerv) ports on localhost.
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
````

### Setup database and datas

```bash
flask --app=dgrehydro setup_schema
flask --app=dgrehydro db upgrade
flask --app=dgrehydro create_pg_functions
flask --app=dgrehydro load_geometries
```

### Ingestion commands

Ideally, ingestion commands should be run in a cron job or similar scheduling system. Here are some examples of how to
run them manually:

```bash
# Riverine floods (HYPE models from FTP)
flask --app=dgrehydro ingest_riverine              # Latest data from all models
flask --app=dgrehydro ingest_riverine 20251212     # Specific date
flask --app=dgrehydro ingest_riverine 20251201 since  # All dates since

# Flash floods
flask --app=dgrehydro ingest_flashflood            # Latest data
flask --app=dgrehydro ingest_flashflood 20251212   # Specific date
flask --app=dgrehydro ingest_flashflood 20251201 since  # All dates since

# POI flow
flask --app=dgrehydro ingest_poiflow               # Ingest from CSV file

# Update specific record
flask --app=dgrehydro update_riverine <subid> <init_date> <forecast_date> <value>
# Example:
flask --app=dgrehydro update_riverine 200384 2025-05-25 2025-05-25 40
```

## Web application (backend API)

#### Development mode

`python3.11 main.py` to run the web server on port `8001`.


#### Routes

##### Riverine Flood
* GET http://localhost:8001/api/v1/riverineflood
* POST http://localhost:8001/api/v1/riverineflood/<subid>

```
  Content-Type: application/json
  {
    "value": 52,
    "init_date": "2025-07-01",
    "forecast_date": "2025-07-01"
  }
```

##### Flash Flood
* GET http://localhost:8001/api/v1/flashflood
* POST http://localhost:8001/api/v1/flashflood/<subid>

```
  Content-Type: application/json
  {
    "value": 52,
    "forecast_date": "2025-07-01"
  }
```

##### POI Flow (Real-time and Forecast)
* GET http://localhost:8001/api/v1/poiflow - Get POI flow data with optional filters
  * Query params: `station_name`, `measurement_date`, `forecast_date`, `realtime_only`
* GET http://localhost:8001/api/v1/poiflow/latest - Get latest real-time measurements for all stations
* GET http://localhost:8001/api/v1/poiflow/stations - Get list of all available stations
* GET http://localhost:8001/api/v1/poiflow/forecast_dates - Get all forecast dates for the latest measurement
* GET http://localhost:8001/api/v1/poiflow/<station_name>/forecast - Get forecast data for a specific station
* POST http://localhost:8001/api/v1/poiflow/<station_name> - Update POI flow data

```
  Content-Type: application/json
  {
    "measurement_date": "2025-10-31T00:00:00",
    "forecast_date": "2025-11-01T00:00:00",
    "flow": 8.867,
    "water_level": 0.436
  }
```

