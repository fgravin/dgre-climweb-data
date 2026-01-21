CREATE OR REPLACE FUNCTION public.dgre_critical_point(
    z integer,
    x integer,
    y integer,
    forecast_date timestamp without time zone)
    RETURNS bytea
    LANGUAGE 'plpgsql'
    COST 100
    STABLE STRICT PARALLEL SAFE
AS $BODY$
DECLARE
    result bytea;
    f_date ALIAS FOR $4;
BEGIN
    WITH
        bounds AS (
            -- Convert tile coordinates to web mercator tile bounds
            SELECT ST_TileEnvelope(z, x, y) AS geom
        ),
        mvt AS (
            SELECT
                ST_AsMVTGeom(ST_Transform(s.geom, 3857), bounds.geom) AS geom,
                o.*,
                CASE
                    WHEN o.water_level_alert = 0 THEN 'Normal'
                    WHEN o.water_level_alert = 1 THEN 'High'
                    WHEN o.water_level_alert = 2 THEN 'Very High'
                    WHEN o.water_level_alert = 3 THEN 'Extremely High'
                    ELSE 'Unknown'
                    END AS level
            FROM public.dgre_critical_point o, bounds, public.dgre_poi_station s
            WHERE o.station_name=s.station_name AND o.forecast_date=f_date
        )
    -- Generate MVT encoding of final input record
    SELECT ST_AsMVT(mvt, 'default')
    INTO result
    FROM mvt;

    RETURN result;
END;
$BODY$;
