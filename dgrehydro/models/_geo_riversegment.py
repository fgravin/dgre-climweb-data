from dgrehydro import db
from geoalchemy2 import Geometry


class RiverSegment(db.Model):
    __tablename__ = "dgre_river_segment"

    subid = db.Column(db.Integer, primary_key=True)
    fid = db.Column(db.Integer, nullable=False)
    geom = db.Column(Geometry(geometry_type="MultiLineString", srid=4326), nullable=False)

    def __init__(self, fid, subid, geom):
        self.fid = fid
        self.subid = subid
        self.geom = geom

    def __repr__(self):
        return '<RiverSegment %r>' % self.fid

    def serialize(self):
        river_segment = {
            "fid": self.fid,
            "subid": self.subid,
        }
        return river_segment
