from sqlalchemy import text, CursorResult
from sqlalchemy.dialects.postgresql import Any

from dgrehydro import db


def riverinesfloods_to_geojson(init_date, forecast_date) -> CursorResult[Any]:

    parameters = {'init_date': init_date, 'forecast_date': forecast_date}
    statement = text("""WITH flood_geom AS (SELECT f.id,
                                                   f.fid,
                                                   f.subid,
                                                   f.init_date,
                                                   f.forecast_date,
                                                   f.init_value,
                                                   f.value,
                                                   s.geom
                                            FROM dgre_riverine_flood f
                                                     JOIN
                                                 dgre_river_segment s
                                                 ON
                                                     f.subid = s.subid
                                            WHERE f.init_date = :init_date
                                              AND f.forecast_date = :forecast_date)
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
