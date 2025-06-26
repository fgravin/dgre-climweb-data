from dgrehydro.models.flashflood import FlashFlood
from dgrehydro.models.riverineflood import RiverineFlood
from dgrehydro.utils import get_dates_from_geojson

def explode_geojson_to_riverineflood(geojson):
    riverine_floods = []

    forecast_dates = get_dates_from_geojson(geojson)
    init_date = forecast_dates[0]

    for feature in geojson['features']:
        for forecast_date in forecast_dates:
            value = feature['properties'][forecast_date.strftime("%Y-%m-%d")]
            fid = feature['properties']["fid"]
            subid = feature['properties']["SUBID"]
            init_value = value
            rf = RiverineFlood(
                fid=fid,
                subid=subid,
                init_date=init_date,
                forecast_date=forecast_date,
                init_value=init_value
            )
            riverine_floods.append(rf)
    return riverine_floods

def explode_geojson_to_flashflood(geojson):
    flash_floods = []

    forecast_dates = get_dates_from_geojson(geojson)
    init_date = forecast_dates[0]

    for feature in geojson['features']:
        for forecast_date in forecast_dates:
            value = feature['properties'][forecast_date.strftime("%Y-%m-%d")]
            fid = feature['properties']["fid"]
            subid = feature['properties']["SUBID"]
            init_value = value
            rf = FlashFlood(
                fid=fid,
                subid=subid,
                init_date=init_date,
                forecast_date=forecast_date,
                init_value=init_value
            )
            flash_floods.append(rf)
    return flash_floods