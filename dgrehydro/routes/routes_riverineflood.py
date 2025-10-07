import datetime
import logging

from flask import request, jsonify
from sqlalchemy import desc

from dgrehydro import db
from dgrehydro.models.riverineflood import RiverineFlood
from dgrehydro.routes import endpoints
from dgrehydro.service.riverine_db import riverinesfloods_to_geojson

FORECAST_DAYS = 10

@endpoints.route('/riverineflood', strict_slashes=False, methods=['GET'])
def get_riverine_floods():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        init_date = request.args.get('init_date', today)
        forecast_date = request.args.get('forecast_date', today)
        logging.info(f"[GET][RIVERINE_FLOOD] init date: {init_date}, forecast date: {forecast_date}")

        query = RiverineFlood.query.filter((RiverineFlood.init_date == init_date) & (RiverineFlood.forecast_date == forecast_date))

        riverine_floods = query.all()
        return [flood.serialize() for flood in riverine_floods], 200
    except Exception as e:
        logging.error(f"Error fetching riverine floods: {e}")
        return {"status": "error", "message": str(e)}, 500

@endpoints.route('/riverineflood/<subid>', strict_slashes=False, methods=['POST'])
def update_riverine_flood(subid):
    try:
        logging.info("[UPDATE][RIVERINE_FLOOD]: Update riverine flood")
        data = request.json
        logging.info(f"[UPDATE][RIVERINE_FLOOD] data: {data}")
        init_date = data.get('init_date')
        forecast_date = data.get('forecast_date')
        value = data.get('value')

        logging.info(f"[UPDATE][RIVERINE_FLOOD] subid: {subid}, init date: {init_date}, forecast date: {forecast_date}, value: {value}")

        db_record_to_update = RiverineFlood.query.filter_by(subid=subid, init_date=init_date, forecast_date=forecast_date).first()

        if db_record_to_update is None:
            logging.error(f"[UPDATE][RIVERINE_FLOOD]: Record not found for subid {subid}, init date {init_date}, forecast date {forecast_date}")
            return {"status": "error", "message": "Record not found"}, 404

        db_record_to_update.value = value
        db.session.commit()

        return db_record_to_update.serialize(), 200

    except Exception as e:
        logging.error(f"[UPDATE][RIVERINE_FLOOD] Error updating riverine flood: {e}")
        return {"status": "error", "message": str(e)}, 500

@endpoints.route('/riverineflood/forecast_dates', strict_slashes=False, methods=['GET'])
def get_riverine_floods_dates():
    try:
        logging.info("[GET][RIVERINE_FLOOD]: get forececast dates")
        latest_init_date = RiverineFlood.query.order_by(desc(RiverineFlood.init_date)).first()
        dates = []

        if latest_init_date:
            latest_init_date = latest_init_date.init_date
            dates.append(latest_init_date)

            for i in range(1, FORECAST_DAYS):
                dates.append(latest_init_date + datetime.timedelta(days=i))

        dates = [date.strftime("%Y-%m-%dT%H:%M:%S.000Z") for date in dates]

        response = {
            "timestamps": dates
        }
        return jsonify(response), 200

    except Exception as e:
        logging.error(f"Error fetching riverine floods: dates {e}")
        return {"status": "error", "message": str(e)}, 500

@endpoints.route('/riverinefloods', strict_slashes=False, methods=['GET'])
def get_riverine_floods_as_geojson():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        init_date = request.args.get('init_date', today)
        forecast_date = request.args.get('forecast_date', today)
        logging.info(f"[GET][RIVERINE_FLOODS AS GEOJSON] init date: {init_date}, forecast date: {forecast_date}")

        result = riverinesfloods_to_geojson(init_date, forecast_date)
        return jsonify(result), 200

    except Exception as e:
        logging.error(f"Error fetching riverine floods: dates {e}")
        return {"status": "error", "message": str(e)}, 500

