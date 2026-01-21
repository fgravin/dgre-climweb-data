import logging

from flask import request, jsonify
from sqlalchemy import desc

from dgrehydro import db
from dgrehydro.models.criticalpoint import CriticalPoint
from dgrehydro.routes import endpoints


@endpoints.route('/criticalpoint', strict_slashes=False, methods=['GET'])
def get_critical_points():
    """
    Get critical point data with optional filters.

    Query parameters:
    - station_name: Filter by station name (Dan, Diarabakoko, Gampela, Heredougou, Nobere, Rakaye)
    - measurement_date: Filter by measurement date (YYYY-MM-DD)
    - forecast_date: Filter by forecast date (YYYY-MM-DD)
    - realtime_only: If 'true', only return real-time data (forecast_date == measurement_date)
    """
    try:
        station_name = request.args.get('station_name')
        measurement_date = request.args.get('measurement_date')
        forecast_date = request.args.get('forecast_date')
        realtime_only = request.args.get('realtime_only', 'false').lower() == 'true'

        logging.info(f"[GET][CRITICAL_POINT] Filters: station={station_name}, measurement_date={measurement_date}, "
                    f"forecast_date={forecast_date}, realtime_only={realtime_only}")

        query = CriticalPoint.query

        if station_name:
            query = query.filter(CriticalPoint.station_name == station_name)

        if measurement_date:
            query = query.filter(db.func.date(CriticalPoint.measurement_date) == measurement_date)

        if forecast_date:
            query = query.filter(db.func.date(CriticalPoint.forecast_date) == forecast_date)

        if realtime_only:
            query = query.filter(CriticalPoint.measurement_date == CriticalPoint.forecast_date)

        # Order by measurement date and station name
        query = query.order_by(desc(CriticalPoint.measurement_date), CriticalPoint.station_name)

        critical_points = query.all()
        return [cp.serialize() for cp in critical_points], 200

    except Exception as e:
        logging.error(f"[GET][CRITICAL_POINT] Error fetching critical points: {e}")
        return {"status": "error", "message": str(e)}, 500


@endpoints.route('/criticalpoint/stations', strict_slashes=False, methods=['GET'])
def get_critical_point_stations():
    """
    Get list of all available critical point stations.
    """
    try:
        stations = db.session.query(CriticalPoint.station_name).distinct().order_by(CriticalPoint.station_name).all()
        station_list = [station[0] for station in stations]

        return jsonify({"stations": station_list}), 200

    except Exception as e:
        logging.error(f"[GET][CRITICAL_POINT] Error fetching stations: {e}")
        return {"status": "error", "message": str(e)}, 500


@endpoints.route('/criticalpoint/latest', strict_slashes=False, methods=['GET'])
def get_latest_critical_points():
    """
    Get the latest real-time measurements for all stations.
    """
    try:
        # Get the most recent measurement date
        latest_measurement = db.session.query(db.func.max(CriticalPoint.measurement_date)).scalar()

        if not latest_measurement:
            return {"status": "error", "message": "No data available"}, 404

        # Get all real-time data (measurement_date == forecast_date) for that date
        query = CriticalPoint.query.filter(
            CriticalPoint.measurement_date == latest_measurement,
            CriticalPoint.measurement_date == CriticalPoint.forecast_date
        ).order_by(CriticalPoint.station_name)

        critical_points = query.all()
        return jsonify({
            "measurement_date": latest_measurement.isoformat(),
            "data": [cp.serialize() for cp in critical_points]
        }), 200

    except Exception as e:
        logging.error(f"[GET][CRITICAL_POINT] Error fetching latest critical points: {e}")
        return {"status": "error", "message": str(e)}, 500


@endpoints.route('/criticalpoint/<station_name>/forecast', strict_slashes=False, methods=['GET'])
def get_critical_point_station_forecast(station_name):
    """
    Get forecast data for a specific station.

    Query parameters:
    - measurement_date: Base date for forecast (defaults to latest)
    """
    try:
        measurement_date = request.args.get('measurement_date')

        logging.info(f"[GET][CRITICAL_POINT] Getting forecast for station: {station_name}, date: {measurement_date}")

        query = CriticalPoint.query.filter(CriticalPoint.station_name == station_name)

        if measurement_date:
            query = query.filter(db.func.date(CriticalPoint.measurement_date) == measurement_date)
        else:
            # Get the latest measurement date for this station
            latest_date = db.session.query(db.func.max(CriticalPoint.measurement_date)).filter(
                CriticalPoint.station_name == station_name
            ).scalar()
            if latest_date:
                query = query.filter(CriticalPoint.measurement_date == latest_date)

        query = query.order_by(CriticalPoint.forecast_date)
        critical_points = query.all()

        if not critical_points:
            return {"status": "error", "message": f"No data found for station {station_name}"}, 404

        return jsonify({
            "station_name": station_name,
            "measurement_date": critical_points[0].measurement_date.isoformat(),
            "forecast": [cp.serialize() for cp in critical_points]
        }), 200

    except Exception as e:
        logging.error(f"[GET][CRITICAL_POINT] Error fetching forecast: {e}")
        return {"status": "error", "message": str(e)}, 500


@endpoints.route('/criticalpoint/<station_name>', strict_slashes=False, methods=['POST'])
def update_critical_point(station_name):
    """
    Update critical point data for a specific station.

    Expected JSON body:
    {
        "measurement_date": "2025-10-31T00:00:00",
        "forecast_date": "2025-10-31T00:00:00",
        "flow": 8.867,
        "water_level": 0.436
    }
    """
    try:
        logging.info(f"[UPDATE][CRITICAL_POINT]: Update critical point for station {station_name}")
        data = request.json
        logging.info(f"[UPDATE][CRITICAL_POINT] data: {data}")

        measurement_date = data.get('measurement_date')
        forecast_date = data.get('forecast_date')
        flow = data.get('flow')
        water_level = data.get('water_level')

        if not measurement_date:
            return {"status": "error", "message": "measurement_date is required"}, 400
        if not forecast_date:
            return {"status": "error", "message": "forecast_date is required"}, 400

        db_record = CriticalPoint.query.filter_by(
            station_name=station_name,
            measurement_date=measurement_date,
            forecast_date=forecast_date
        ).first()

        if db_record is None:
            logging.error(f"[UPDATE][CRITICAL_POINT]: Record not found for {station_name} at {measurement_date} with forecast_date {forecast_date}")
            return {"status": "error", "message": "Record not found"}, 404

        if flow is not None:
            db_record.flow = flow
        if water_level is not None:
            db_record.water_level = water_level

        db.session.commit()

        return db_record.serialize(), 200

    except Exception as e:
        logging.error(f"[UPDATE][CRITICAL_POINT] Error updating critical point: {e}")
        return {"status": "error", "message": str(e)}, 500


@endpoints.route('/criticalpoint/forecast_dates', strict_slashes=False, methods=['GET'])
def get_critical_point_measurement_dates():
    """
    Get list of all forecast dates for the latest measurement date.
    Returns the forecast horizons (real-time + 11 days) for the most recent measurement.
    """
    try:
        logging.info("[GET][CRITICAL_POINT]: Get forecast dates for latest measurement")

        # Get the latest measurement date
        latest_measurement = db.session.query(db.func.max(CriticalPoint.measurement_date)).scalar()

        if not latest_measurement:
            return {"status": "error", "message": "No data available"}, 404

        # Get all distinct forecast dates for the latest measurement date
        forecast_dates = db.session.query(CriticalPoint.forecast_date).filter(
            CriticalPoint.measurement_date == latest_measurement
        ).distinct().order_by(CriticalPoint.forecast_date).all()

        date_list = [date[0].strftime("%Y-%m-%dT%H:%M:%S.000Z") for date in forecast_dates]

        response = {
            "measurement_date": latest_measurement.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "timestamps": date_list,
            "count": len(date_list)
        }
        return jsonify(response), 200

    except Exception as e:
        logging.error(f"[GET][CRITICAL_POINT] Error fetching forecast dates: {e}")
        return {"status": "error", "message": str(e)}, 500
