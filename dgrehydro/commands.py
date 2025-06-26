import logging
import click

from sqlalchemy.sql import text
from dgrehydro import db
from dgrehydro.ingestion import explode_geojson_to_riverineflood, explode_geojson_to_flashflood
from dgrehydro.models.riverineflood import RiverineFlood
from dgrehydro.utils import load_riverine_flood_geojson

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

@click.command(name="ingest_riverine")
def ingest_riverine():
    logging.info("[INGESTION][RIVERINE]: Start")
    logging.info("[INGESTION][RIVERINE]: Load geojson")
    geojson = load_riverine_flood_geojson()

    logging.info("[INGESTION][RIVERINE]: Ingest in base")
    db_riverine_floods = explode_geojson_to_riverineflood(geojson)
    for db_riverine_flood in db_riverine_floods :
        db.session.add(db_riverine_flood)

    db.session.flush(db_riverine_floods)
    db.session.commit()

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

@click.command(name="ingest_flash")
def ingest_flash():
    logging.info("[INGESTION][FLASH]: Start")
    logging.info("[INGESTION][FLASH]: Load geojson")
    geojson = load_riverine_flood_geojson()

    logging.info("[INGESTION][FLASH]: Ingest in base")
    db_flash_floods = explode_geojson_to_flashflood(geojson)
    for db_flash_flood in db_flash_floods :
        db.session.add(db_flash_flood)

    db.session.flush(db_flash_floods)
    db.session.commit()