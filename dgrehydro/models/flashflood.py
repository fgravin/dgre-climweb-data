from dgrehydro import db

class FlashFlood(db.Model):
    __tablename__ = "dgre_flash_flood"
    __table_args__ = (
        db.UniqueConstraint("subid", "init_date", "forecast_date", name='unique_flash_flood_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    fid = db.Column(db.Integer, nullable=False)
    subid = db.Column(db.String, nullable=False)
    init_date = db.Column(db.DateTime, nullable=False)
    forecast_date = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    init_value = db.Column(db.Integer, nullable=False)

    def __init__(self, fid, subid, init_date, forecast_date, init_value):
        self.fid = fid
        self.subid = subid
        self.init_date = init_date
        self.forecast_date = forecast_date
        self.value = init_value
        self.init_value = init_value

    def __repr__(self):
        return '<FlashFlood %r>' % self.id

    def serialize(self):
        flash_flood = {
            "id": self.id,
            "fid": self.fid,
            "subid": self.subid,
            "init_date": self.init_date,
            "forecast_date": self.forecast_date,
            "init_value": self.init_value,
            "value": self.value,
        }
        return flash_flood
