CREATE OR REPLACE FUNCTION public.dgre_flash_flood(
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
                    WHEN o.value = 0 THEN 'Normal'
                    WHEN o.value = 1 THEN 'High'
                    WHEN o.value = 2 THEN 'Very High'
                    WHEN o.value = 3 THEN 'Extremely High'
                    ELSE 'Unknown'
                    END AS level
            FROM public.dgre_flash_flood o, bounds, public.dgre_municipality s
            WHERE o.subid=s.subid AND o.forecast_date=f_date
        )
    -- Generate MVT encoding of final input record
    SELECT ST_AsMVT(mvt, 'default')
    INTO result
    FROM mvt;

    RETURN result;
END;
$BODY$;
