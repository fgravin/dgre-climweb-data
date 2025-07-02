from dgrehydro import db


class RiverineFlood(db.Model):
    __tablename__ = "dgre_riverine_flood"
    __table_args__ = (
        db.UniqueConstraint("subid", "init_date", "forecast_date", name='unique_riverine_flood_date'),
    )
    id = db.Column(db.Integer, primary_key=True)
    fid = db.Column(db.Integer, nullable=False)
    subid = db.Column(db.String, nullable=False)
    init_date = db.Column(db.DateTime, nullable=False)
    forecast_date = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    init_value = db.Column(db.Integer, nullable=False)

    def __init__(self, fid, subid, init_date, forecast_date, init_value, value):
        self.fid = fid
        self.subid = subid
        self.init_date = init_date
        self.forecast_date = forecast_date
        self.value = value
        self.init_value = init_value

    def __repr__(self):
        return '<RiverineFlood %r>' % self.id

    def serialize(self):
        riverine_flood = {
            "id": self.id,
            "fid": self.fid,
            "subid": self.subid,
            "init_date": self.init_date,
            "forecast_date": self.forecast_date,
            "init_value": self.init_value,
            "value": self.value,
        }
        return riverine_flood
