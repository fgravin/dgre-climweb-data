from geoalchemy2 import Geometry

from dgrehydro import db

class GeoRegion(db.Model):
    __tablename__ = "dgre_geo_region"

    gid = db.Column(db.String(256), primary_key=True)
    country_iso = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    geom = db.Column(Geometry(geometry_type="MultiPolygon", srid=4326), nullable=False)

    def __init__(self, gid, country_iso, name, geom):
        self.gid = gid
        self.country_iso = country_iso
        self.name = name
        self.geom = geom

    def __repr__(self):
        return '<GeoRegion %r>' % self.name

    def serialize(self):
        """Return object data in easily serializable format"""
        geo_region = {
            "gid": self.gid,
            "name": self.name,
            "country_iso": self.country_iso
        }

        return geo_region
