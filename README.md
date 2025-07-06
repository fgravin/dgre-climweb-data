# DGRE Hydro

This is a web application for managing and visualizing hydrological data, for DGRE in Burkina Faso. It provides
functionalities to ingest, update, and visualize flood data.

## Get started

Copy `.env.sample` to `.env` and fill in the required values.

### Setup the environment

```bash
python3.11 -m venv .venv
poetry install
source .venv/bin/activate
```

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
flask --app=dgregydro ingest_flash_flood
flask --app=dgrehydro update_riverine 200384 2025-05-25 2025-05-25 40
```

### Web application

#### Development mode

`python3.11 main.py` to run the web server on `FLASK_APP_PORT` (default is `5000`).


#### Production mode

To run in production, you can use `gunicorn` or `uwsgi` with the Flask app.

```bash
poetry add gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

#### Routes

* GET http://localhost:5000/api/v1/riverineflood
* POST http://localhost:5000/api/v1/riverineflood/<subid>

```
  Content-Type: application/json
  {
    "value": 52,
    "init_date": "2025-07-01",
    "forecast_date": "2025-07-01"
  }
```

* GET http://localhost:5000/api/v1/flashflood
* POST http://localhost:5000/api/v1/flashflood/<subid>

```
  Content-Type: application/json
  {
    "value": 52,
    "forecast_date": "2025-07-01"
  }
```

