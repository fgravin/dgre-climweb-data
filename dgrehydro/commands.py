import logging
import os
import re

import click
from sqlalchemy.sql import text

from dgrehydro import db
from dgrehydro.ingestors.burkina.geometries_loader import load_river_segments, load_municipalities
from dgrehydro.ingestors.burkina.ingestor_flashflood import ingest_flash_floods_from_csv
from dgrehydro.ingestors.burkina.ingestor_riverine import ingest_riverine_floods_from_csv
from dgrehydro.models.riverineflood import RiverineFlood


@click.command(name="setup_schema")
def setup_schema():
    logging.info("[DBSETUP]: Setting up schema")
    schema_sql = f"""DO
                $do$
                BEGIN
                    CREATE EXTENSION IF NOT EXISTS postgis;
                    CREATE SCHEMA IF NOT EXISTS dgre_hydro;
                END
                $do$;"""
    
    db.session.execute(text(schema_sql))
    db.session.commit()
    
    logging.info("[DBSETUP]: Done Setting up schema")

@click.command(name="create_pg_functions")
def create_pg_functions():
    logging.info("[DBSETUP]: Creating pg functions")

    # Run all sql scripts in dgrehydro/db/ folder
    sql_files_directory = './dgrehydro/db/'
    for filename in os.listdir(sql_files_directory):
        if re.search(r'\.sql$', filename):
            sql_file_path = os.path.join(sql_files_directory, filename)
            try:
                with open(sql_file_path, 'r') as file:
                    sql_script = file.read()
                    db.session.execute(text(sql_script))
                    db.session.commit()
                    logging.info(f"[DBSETUP]: Executed SQL script from {sql_file_path}")
            except Exception as e:
                logging.error(f"[DBSETUP]: Error executing {sql_file_path}: {e}")
    logging.info("[DBSETUP]: Done Creating pg function")

@click.command(name="ingest_riverine")
def ingest_riverine():
    logging.info("[INGESTION][RIVERINE]: Start")
    ingest_riverine_floods_from_csv()

@click.command(name="update_riverine")
@click.argument("subid")
@click.argument("init_date")
@click.argument("forecast_date")
@click.argument("value")
def update_riverine(subid, init_date, forecast_date, value):
    logging.info("[UPDATE][RIVERINE]: Start")
    logging.info("[UPDATE][RIVERINE]: Load geojson")

    db_record_to_update = RiverineFlood.query.filter_by(subid=subid, init_date=init_date, forecast_date=forecast_date).first()

    if db_record_to_update is None:
        logging.info(f"[UPDATE][RIVERINE]: Error while fetching {subid} {init_date} {forecast_date}")
        return

    logging.info("[UPDATE][RIVERINE]: Update record")
    db_record_to_update.value = value
    db.session.commit()

@click.command(name="load_geometries")
def load_geometries():
    load_river_segments()
    load_municipalities()

@click.command(name="ingest_flashflood")
def ingest_flashflood():
    logging.info("[INGESTION][FLASHFLOOD]: Start")
    ingest_flash_floods_from_csv()
