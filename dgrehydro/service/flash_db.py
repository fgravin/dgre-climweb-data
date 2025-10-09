from sqlalchemy import text, CursorResult
from sqlalchemy.dialects.postgresql import Any

from dgrehydro import db


def flashfloods_to_geojson(forecast_date) -> CursorResult[Any]:
    parameters = {'forecast_date': forecast_date}
    statement = text("""WITH flood_geom AS (SELECT f.id,
                                                   f.fid,
                                                   f.subid,
                                                   f.forecast_date,
                                                   f.init_value,
                                                   f.value,
                                                   s.adm2_fr,
                                                   s.adm3_fr,
                                                   s.geom
                                            FROM dgre_flash_flood f
                                                     JOIN
                                                 dgre_municipality s
                                                 ON
                                                     f.subid = s.subid
                                            WHERE f.forecast_date = :forecast_date)
                        SELECT jsonb_build_object(
                                       'type', 'FeatureCollection',
                                       'features', jsonb_agg(
                                               jsonb_build_object(
                                                       'type', 'Feature',
                                                       'geometry', ST_AsGeoJSON(geom, 4326)::jsonb,
                                                       'properties', to_jsonb(t) - 'geom'
                                               )
                                                   )
                               ) AS geojson
                        FROM flood_geom t;
                     """)
    return db.session.execute(statement, parameters).scalar()
