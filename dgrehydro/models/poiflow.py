from dgrehydro import db


class PoiFlow(db.Model):
    __tablename__ = "dgre_poi_flow"
    __table_args__ = (
        db.UniqueConstraint("station_name", "measurement_date", "forecast_date", name='unique_poi_flow_measurement'),
    )

    id = db.Column(db.Integer, primary_key=True)
    station_name = db.Column(db.String, nullable=False)
    measurement_date = db.Column(db.DateTime, nullable=False)
    forecast_date = db.Column(db.DateTime, nullable=False)
    flow = db.Column(db.Float, nullable=True)
    water_level = db.Column(db.Float, nullable=True)

    def __init__(self, station_name, measurement_date, forecast_date, flow, water_level):
        self.station_name = station_name
        self.measurement_date = measurement_date
        self.forecast_date = forecast_date
        self.flow = flow
        self.water_level = water_level

    def __repr__(self):
        return f'<PoiFlow {self.station_name} - {self.forecast_date}>'

    @property
    def is_realtime(self):
        """Check if this is a real-time measurement (forecast_date == measurement_date)"""
        return self.forecast_date == self.measurement_date

    @property
    def forecast_horizon_hours(self):
        """Calculate forecast horizon in hours"""
        if self.forecast_date and self.measurement_date:
            delta = self.forecast_date - self.measurement_date
            return delta.total_seconds() / 3600
        return 0

    @property
    def forecast_horizon_days(self):
        """Calculate forecast horizon in days"""
        return self.forecast_horizon_hours / 24 if self.forecast_horizon_hours else 0

    def serialize(self):
        poi_flow = {
            "id": self.id,
            "station_name": self.station_name,
            "measurement_date": self.measurement_date.isoformat() if self.measurement_date else None,
            "forecast_date": self.forecast_date.isoformat() if self.forecast_date else None,
            "flow": self.flow,
            "water_level": self.water_level,
            "is_realtime": self.is_realtime,
            "forecast_horizon_hours": self.forecast_horizon_hours,
            "forecast_horizon_days": round(self.forecast_horizon_days, 2)
        }
        return poi_flow
