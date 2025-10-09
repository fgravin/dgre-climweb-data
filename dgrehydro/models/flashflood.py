from dgrehydro import db

class FlashFlood(db.Model):
    __tablename__ = "dgre_flash_flood"
    __table_args__ = (
        db.UniqueConstraint("subid", "forecast_date", name='unique_flash_flood_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    fid = db.Column(db.Integer, nullable=False)
    subid = db.Column(db.Integer, nullable=False)
    adm3_fr = db.Column(db.String, nullable=False)
    forecast_date = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    init_value = db.Column(db.Integer, nullable=False)
    weighted_ffft = db.Column(db.Float, nullable=False)

    def __init__(self, fid, subid, adm3_fr, forecast_date, init_value, value, weighted_ffft):
        self.fid = fid
        self.subid = subid
        self.adm3_fr = adm3_fr
        self.forecast_date = forecast_date
        self.value = value
        self.init_value = init_value
        self.weighted_ffft = weighted_ffft

    def __repr__(self):
        return '<FlashFlood %r>' % self.id

    def serialize(self):
        flash_flood = {
            "id": self.id,
            "fid": self.fid,
            "subid": self.subid,
            "adm3_fr": self.adm3_fr,
            "forecast_date": self.forecast_date,
            "init_value": self.init_value,
            "value": self.value,
            "weighted_ffft": self.weighted_ffft,
        }
        return flash_flood
