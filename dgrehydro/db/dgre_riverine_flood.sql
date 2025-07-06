CREATE OR REPLACE FUNCTION public.dgre_riverine_flood(
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
    initial_date timestamp without time zone;
    f_date ALIAS FOR $4;
BEGIN
    -- If initial_date is not provided, determine the latest available, minus 1
    SELECT MAX(init_date) INTO initial_date
    FROM public.dgre_riverine_flood;

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
                    WHEN o.value = 0 THEN 'Normal'
                    WHEN o.value = 1 THEN 'High'
                    WHEN o.value = 2 THEN 'Very High'
                    WHEN o.value = 3 THEN 'Extremely High'
                    ELSE 'Unknown'
                    END AS level
            FROM public.dgre_riverine_flood o, bounds, public.dgre_river_segment s
            WHERE o.subid=s.subid AND o.init_date=initial_date AND o.forecast_date=f_date
        )
    -- Generate MVT encoding of final input record
    SELECT ST_AsMVT(mvt, 'default')
    INTO result
    FROM mvt;

    RETURN result;
END;
$BODY$;