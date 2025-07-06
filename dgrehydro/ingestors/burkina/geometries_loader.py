import json
import logging
import os
from sqlalchemy import func

from dgrehydro import db
from dgrehydro.models.municipality import Municipality
from dgrehydro.models.riversegment import RiverSegment

GEOMETRIES_DATA_DIR = './dgrehydro/data'
RIVER_SEGMENTS_GEOJSON_FILE = 'bfa12_river_segments.geojson'
MUNICIPALITIES_GEOJSON_FILE = 'bfa12_municipalities.geojson'

def load_river_segments():
    logging.info("[GEOMETRIES LOADING][SEGMENTS]: Loading river segments")

    if not os.path.exists(GEOMETRIES_DATA_DIR):
        logging.error("[GEOMETRIES LOADING][SEGMENTS]: Geometries data directory does not exist")
        return

    geojson_file = os.path.join(GEOMETRIES_DATA_DIR, RIVER_SEGMENTS_GEOJSON_FILE)

    if not os.path.exists(geojson_file):
        logging.error(f"[GEOMETRIES LOADING][SEGMENTS]: File {geojson_file} does not exist")
        return

    logging.info(f"[GEOMETRIES LOADING][SEGMENTS]: Loading {geojson_file}")

    with open(geojson_file, "r") as f:
        geojson = json.load(f)

        features = geojson.get("features")

        for feature in features:
            props = feature.get("properties")
            geom = feature.get("geometry")
            fid = props.get("fid")
            subid = props.get("SUBID")

            river_segment_data = {
                "fid": fid,
                "subid": subid,
                "geom": func.ST_GeomFromGeoJSON(json.dumps(geom))
            }

            db_river_segment = RiverSegment.query.get(river_segment_data.get("subid"))
            exists = False

            if db_river_segment:
                exists = True

            db_river_segment = RiverSegment(**river_segment_data)

            if exists:
                logging.info('[GEOMETRIES LOADING][SEGMENTS]: UPDATE')
                db.session.merge(db_river_segment)
            else:
                logging.info('[GEOMETRIES LOADING][SEGMENTS]: ADD')
                db.session.add(db_river_segment)

        db.session.commit()
        logging.info('[GEOMETRIES LOADING][SEGMENTS]: Done')

def load_municipalities():
    logging.info("[GEOMETRIES LOADING][MUNICIPALITIES]: Loading municipalities")

    if not os.path.exists(GEOMETRIES_DATA_DIR):
        logging.error("[GEOMETRIES LOADING][MUNICIPALITIES]: Geometries data directory does not exist")
        return

    geojson_file = os.path.join(GEOMETRIES_DATA_DIR, MUNICIPALITIES_GEOJSON_FILE)

    if not os.path.exists(geojson_file):
        logging.error(f"[GEOMETRIES LOADING][MUNICIPALITIES]: File {geojson_file} does not exist")
        return

    logging.info(f"[GEOMETRIES LOADING][MUNICIPALITIES]: Loading {geojson_file}")

    with open(geojson_file, "r") as f:
        geojson = json.load(f)

        features = geojson.get("features")

        for feature in features:
            props = feature.get("properties")
            geom = feature.get("geometry")

            geom_type = geom.get("type")
            if geom_type == "Polygon":
                geom = {
                    "type": "MultiPolygon",
                    "coordinates": [geom.get("coordinates")]
                }

            subid = props.get("SUBID")
            adm3_fr = props.get("ADM3_FR")
            adm2_fr = props.get("ADM2_FR")

            municipality = {
                "subid": subid,
                "adm3_fr": adm3_fr,
                "adm2_fr": adm2_fr,
                "geom": func.ST_GeomFromGeoJSON(json.dumps(geom))
            }

            db_municipality = Municipality.query.get(subid)
            exists = False

            if db_municipality:
                exists = True

            db_municipality = Municipality(**municipality)

            if exists:
                logging.info('[GEOMETRIES LOADING][MUNICIPALITIES]: UPDATE')
                db.session.merge(db_municipality)
            else:
                logging.info('[GEOMETRIES LOADING][MUNICIPALITIES]: ADD')
                db.session.add(db_municipality)

        db.session.commit()
        logging.info('[GEOMETRIES LOADING][MUNICIPALITIES]: Done')

