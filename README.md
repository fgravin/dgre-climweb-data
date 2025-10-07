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
flask --app=dgrehydro ingest_riverine
flask --app=dgregydro ingest_flashflood
flask --app=dgrehydro update_riverine 200384 2025-05-25 2025-05-25 40
```

## Web application (backend API)

#### Development mode

`python3.11 main.py` to run the web server on port `8001`.


#### Routes

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

* GET http://localhost:8001/api/v1/flashflood
* POST http://localhost:8001/api/v1/flashflood/<subid>

```
  Content-Type: application/json
  {
    "value": 52,
    "forecast_date": "2025-07-01"
  }
```

