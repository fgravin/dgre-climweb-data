import json
import logging
import os

from sqlalchemy import func

from dgrehydro import db
from dgrehydro.config.country_config import country_config
from dgrehydro.models._geo_municipality import Municipality
from dgrehydro.models._geo_region import GeoRegion
from dgrehydro.models._geo_riversegment import RiverSegment

GEOMETRIES_DATA_DIR = './dgrehydro/_static_data/geo'
RIVER_SEGMENTS_GEOJSON_FILE = 'bfa12_river_segments.geojson'
MUNICIPALITIES_GEOJSON_FILE = 'bfa_adm3.geojson'
REGIONS_GEOJSON_FILE = 'bfa_regions.geojson'

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

            subid = props.get("subid")
            adm3_fr = props.get("adm3_fr")
            adm2_fr = props.get("adm2_fr")

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


def load_regions():
    logging.info("[GEOMETRIES LOADING][REGIONS]: Loading regions")

    if not os.path.exists(GEOMETRIES_DATA_DIR):
        logging.info("[GEOMETRIES LOADING][REGIONS]: Geometries data directory does not exist")
        return

    config = country_config.get('BFA')

    iso = config.get("iso")

    logging.info("[GEOMETRIES LOADING][REGIONS]: Loading boundaries for {}".format('BFA'))

    geojson_file = os.path.join(GEOMETRIES_DATA_DIR, f"{iso.lower()}_regions.geojson")

    if not os.path.exists(geojson_file):
        logging.info(f"[GEOMETRIES LOADING][REGIONS]: File {geojson_file} does not exist")
        return

    logging.info(f"[GEOMETRIES LOADING][REGIONS]: Loading {geojson_file}")

    id_field = config.get("id_field")
    name_field = config.get("name_field")

    with open(geojson_file, "r") as f:
        geojson = json.load(f)

        features = geojson.get("features")

        for feature in features:
            props = feature.get("properties")

            id_prop = props.get(id_field)
            name = props.get(name_field)

            if id_prop is None and name is None:
                logging.info(f"[REGION]: Skipping ")
                continue

            gid = f"{iso}_{id_prop}"

            geom = feature.get("geometry")
            geom_type = geom.get("type")

            # convert to multipolygon
            if geom_type == "Polygon":
                geom = {
                    "type": "MultiPolygon",
                    "coordinates": [geom.get("coordinates")]
                }

                georegion_data = {
                    "gid": gid,
                    "country_iso": iso,
                    "name": name,
                    "geom": func.ST_GeomFromGeoJSON(json.dumps(geom))
                }

                db_georegion = GeoRegion.query.get(georegion_data.get("gid"))
                exists = False

                if db_georegion:
                    exists = True

                db_georegion = GeoRegion(**georegion_data)

                if exists:
                    logging.info('[REGION]: UPDATE')
                    db.session.merge(db_georegion)
                else:
                    logging.info('[REGION]: ADD')
                    db.session.add(db_georegion)

                db.session.commit()
