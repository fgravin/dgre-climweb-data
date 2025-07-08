import datetime
import logging

from flask import request, jsonify
from sqlalchemy import desc

from dgrehydro import db
from dgrehydro.models.flashflood import FlashFlood
from dgrehydro.routes import endpoints


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

@endpoints.route('/flashflood/forecast_dates', strict_slashes=False, methods=['GET'])
def get_flash_flood_dates():
    try:
        logging.info("[GET][FLASH_FLOOD]: get forececast dates")
        db_flashflood = FlashFlood.query.order_by(desc(FlashFlood.forecast_date)).first()
        dates = []

        if db_flashflood:
            latest_date = db_flashflood.forecast_date
            dates.append(latest_date)

            for i in range(1, 4):
                dates.append(latest_date - datetime.timedelta(hours=i*6))

        dates = [date.strftime("%Y-%m-%dT%H:%M:%S.000Z") for date in dates]

        response = {
            "timestamps": dates
        }
        return jsonify(response), 200

    except Exception as e:
        logging.error(f"Error fetching flash floods dates: {e}")
        return {"status": "error", "message": str(e)}, 500
