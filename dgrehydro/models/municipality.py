from geoalchemy2 import Geometry

from dgrehydro import db


class Municipality(db.Model):
    __tablename__ = "dgre_municipality"

    subid = db.Column(db.Integer(), primary_key=True)
    adm3_fr = db.Column(db.String(256), nullable=False)
    adm2_fr = db.Column(db.String(256), nullable=False)
    geom = db.Column(Geometry(geometry_type="MultiPolygon", srid=4326), nullable=False)

    def __init__(self, subid, adm3_fr, adm2_fr, geom):
        self.subid = subid
        self.adm3_fr = adm3_fr
        self.adm2_fr = adm2_fr
        self.geom = geom

    def __repr__(self):
        return '<Municipality %r>' % self.subid

    def serialize(self):
        municipality = {
            "subid": self.subid,
            "adm3_fr": self.adm3_fr,
            "adm2_fr": self.adm2_fr,
        }
        return municipality
