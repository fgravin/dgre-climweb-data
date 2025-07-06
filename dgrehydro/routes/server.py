import datetime
import logging

from flask import request

from dgrehydro import db
from dgrehydro.models.flashflood import FlashFlood
from dgrehydro.models.riverineflood import RiverineFlood
from dgrehydro.routes import endpoints

# http://localhost:5000/api/v1/riverineflood?=init_date=2025-07-01&forecast_date=2025-07-01
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

@endpoints.route('/flashflood', strict_slashes=False, methods=['GET'])
def get_flash_floods():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        forecast_date = request.args.get('forecast_date', today)
        logging.info(f"[GET][FLASH_FLOOD] forecast date: {forecast_date}")

        query = FlashFlood.query.filter(FlashFlood.forecast_date == forecast_date)

        flash_floods = query.all()
        return [flood.serialize() for flood in flash_floods], 200
    except Exception as e:
        logging.error(f"Error fetching flash floods: {e}")
        return {"status": "error", "message": str(e)}, 500

@endpoints.route('/flashflood/<subid>', strict_slashes=False, methods=['POST'])
def update_flash_flood(subid):
    try:
        logging.info("[UPDATE][FLASH_FLOOD]: Update flash flood")
        data = request.json
        logging.info(f"[UPDATE][FLASH_FLOOD] data: {data}")
        forecast_date = data.get('forecast_date')
        value = data.get('value')

        logging.info(f"[UPDATE][FLASH_FLOOD] subid: {subid},forecast date: {forecast_date}, value: {value}")

        db_record_to_update = FlashFlood.query.filter_by(subid=subid, forecast_date=forecast_date).first()

        if db_record_to_update is None:
            logging.error(f"[UPDATE][FLASH_FLOOD]: Record not found for subid {subid}, forecast date {forecast_date}")
            return {"status": "error", "message": "Record not found"}, 404

        db_record_to_update.value = value
        db.session.commit()

        return db_record_to_update.serialize(), 200

    except Exception as e:
        logging.error(f"[UPDATE][FLASH_FLOOD] Error updating flash flood: {e}")
        return {"status": "error", "message": str(e)}, 500
