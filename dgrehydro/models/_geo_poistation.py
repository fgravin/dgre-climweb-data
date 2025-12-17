from geoalchemy2 import Geometry
from sqlalchemy import Column, String, Float

from dgrehydro import db


class PoiStation(db.Model):
    __tablename__ = "dgre_poi_station"

    station_name = Column(String(256), primary_key=True)
    name_fr = Column(String(256))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))

    def __init__(self, station_name, name_fr, latitude, longitude, geom):
        self.station_name = station_name
        self.name_fr = name_fr
        self.latitude = latitude
        self.longitude = longitude
        self.geom = geom

    def __repr__(self):
        return f'<PoiStation {self.station_name}>'

    def serialize(self):
        return {
            "station_name": self.station_name,
            "name_fr": self.name_fr,
            "latitude": self.latitude,
            "longitude": self.longitude
        }
