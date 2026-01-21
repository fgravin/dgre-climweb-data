-- First, create a table to store POI station geometries
-- This should be populated with actual station coordinates
CREATE TABLE IF NOT EXISTS public.dgre_poi_station (
    station_name VARCHAR(256) PRIMARY KEY,
    name_fr VARCHAR(256),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326)
);

-- Create a spatial index on the geometry column
CREATE INDEX IF NOT EXISTS idx_dgre_poi_station_geom ON public.dgre_poi_station USING GIST (geom);

-- Function to generate POI station geometries from lat/lon
CREATE OR REPLACE FUNCTION public.update_poi_station_geom()
    RETURNS TRIGGER
    LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$BODY$;

-- Trigger to automatically update geometry when lat/lon changes
DROP TRIGGER IF EXISTS trigger_update_poi_station_geom ON public.dgre_poi_station;
CREATE TRIGGER trigger_update_poi_station_geom
    BEFORE INSERT OR UPDATE ON public.dgre_poi_station
    FOR EACH ROW
    EXECUTE FUNCTION public.update_poi_station_geom();

-- Main function to generate MVT tiles for critical point data
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
    latest_measurement timestamp without time zone;
    f_date ALIAS FOR $4;
BEGIN
    -- Get the latest measurement date
    SELECT MAX(measurement_date) INTO latest_measurement
    FROM public.dgre_critical_point;

    WITH
        bounds AS (
            -- Convert tile coordinates to web mercator tile bounds
            SELECT ST_TileEnvelope(z, x, y) AS geom
        ),
        mvt AS (
            SELECT
                ST_AsMVTGeom(ST_Transform(s.geom, 3857), bounds.geom) AS geom,
                s.station_name,
                s.name_fr,
                cp.flow,
                cp.water_level,
                cp.measurement_date,
                cp.forecast_date,
                -- Calculate if this is real-time data
                CASE
                    WHEN cp.measurement_date = cp.forecast_date THEN true
                    ELSE false
                END AS is_realtime,
                -- Calculate forecast horizon in hours
                EXTRACT(EPOCH FROM (cp.forecast_date - cp.measurement_date)) / 3600 AS forecast_horizon_hours,
                -- Add flow level classification (customize thresholds as needed)
                CASE
                    WHEN cp.flow IS NULL THEN 'No Data'
                    WHEN cp.flow < 5 THEN 'Low'
                    WHEN cp.flow < 15 THEN 'Normal'
                    WHEN cp.flow < 30 THEN 'High'
                    WHEN cp.flow < 50 THEN 'Very High'
                    ELSE 'Extremely High'
                END AS flow_level,
                -- Add water level classification (customize thresholds as needed)
                CASE
                    WHEN cp.water_level IS NULL THEN 'No Data'
                    WHEN cp.water_level < 0.5 THEN 'Low'
                    WHEN cp.water_level < 1.0 THEN 'Normal'
                    WHEN cp.water_level < 1.5 THEN 'High'
                    ELSE 'Very High'
                END AS water_level_class
            FROM public.dgre_critical_point cp
            INNER JOIN public.dgre_poi_station s ON cp.station_name = s.station_name
            CROSS JOIN bounds
            WHERE cp.measurement_date = latest_measurement
                AND cp.forecast_date = f_date
                AND ST_Intersects(s.geom, ST_Transform(bounds.geom, 4326))
        )
    -- Generate MVT encoding of final input record
    SELECT ST_AsMVT(mvt, 'default')
    INTO result
    FROM mvt;

    RETURN result;
END;
$BODY$;

COMMENT ON FUNCTION public.dgre_critical_point(integer, integer, integer, timestamp without time zone)
IS 'Generate Mapbox Vector Tile for critical point data at a given zoom, x, y tile coordinates and forecast date. Returns flow and water level data for the latest measurement date.';

-- Function to get critical point data as GeoJSON (without tiling)
CREATE OR REPLACE FUNCTION public.dgre_critical_point_geojson(
    forecast_date timestamp without time zone)
    RETURNS json
    LANGUAGE 'plpgsql'
    COST 100
    STABLE STRICT PARALLEL SAFE
AS $BODY$
DECLARE
    result json;
    latest_measurement timestamp without time zone;
    f_date ALIAS FOR $1;
BEGIN
    -- Get the latest measurement date
    SELECT MAX(measurement_date) INTO latest_measurement
    FROM public.dgre_critical_point;

    WITH features AS (
        SELECT
            'Feature' AS type,
            ST_AsGeoJSON(s.geom)::json AS geometry,
            json_build_object(
                'station_name', s.station_name,
                'name_fr', s.name_fr,
                'flow', cp.flow,
                'water_level', cp.water_level,
                'measurement_date', cp.measurement_date,
                'forecast_date', cp.forecast_date,
                'is_realtime', (cp.measurement_date = cp.forecast_date),
                'forecast_horizon_hours', EXTRACT(EPOCH FROM (cp.forecast_date - cp.measurement_date)) / 3600,
                'flow_level', CASE
                    WHEN cp.flow IS NULL THEN 'No Data'
                    WHEN cp.flow < 5 THEN 'Low'
                    WHEN cp.flow < 15 THEN 'Normal'
                    WHEN cp.flow < 30 THEN 'High'
                    WHEN cp.flow < 50 THEN 'Very High'
                    ELSE 'Extremely High'
                END,
                'water_level_class', CASE
                    WHEN cp.water_level IS NULL THEN 'No Data'
                    WHEN cp.water_level < 0.5 THEN 'Low'
                    WHEN cp.water_level < 1.0 THEN 'Normal'
                    WHEN cp.water_level < 1.5 THEN 'High'
                    ELSE 'Very High'
                END
            ) AS properties
        FROM public.dgre_critical_point cp
        INNER JOIN public.dgre_poi_station s ON cp.station_name = s.station_name
        WHERE cp.measurement_date = latest_measurement
            AND cp.forecast_date = f_date
    )
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(json_agg(features), '[]'::json)
    )
    INTO result
    FROM features;

    RETURN result;
END;
$BODY$;

COMMENT ON FUNCTION public.dgre_critical_point_geojson(timestamp without time zone)
IS 'Generate GeoJSON FeatureCollection for critical point data at a given forecast date. Returns all stations with their flow and water level data for the latest measurement date.';
