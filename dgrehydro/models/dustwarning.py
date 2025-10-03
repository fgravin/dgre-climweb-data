from dgrehydro import db

class DustWarning(db.Model):
    __tablename__ = "dgre_dust_warning"
    __table_args__ = (
        db.UniqueConstraint("gid", "init_date", "forecast_date", name='unique_dust_warming_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(db.String(256), db.ForeignKey('dgre_geo_region.gid', ondelete="CASCADE"), nullable=False)
    init_date = db.Column(db.DateTime, nullable=False)
    forecast_date = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.Integer, nullable=False)

    def __init__(self, gid, init_date, forecast_date, value):
        self.gid = gid
        self.init_date = init_date
        self.forecast_date = forecast_date
        self.value = value

    def __repr__(self):
        return '<DustWarning %r>' % self.id

    def serialize(self):
        """Return object data in easily serializable format"""
        dust_warning = {
            "id": self.id,
            "gid": self.gid,
            "init_date": self.init_date,
            "forecast_date": self.forecast_date,
            "value": self.value,
        }

        return dust_warning
