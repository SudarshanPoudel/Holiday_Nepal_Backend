from sqlalchemy import Column, Integer, String, ForeignKey, Float, event
from app.database.database import Base
from geoalchemy2 import Geography
from  geoalchemy2.shape import from_shape
from shapely.geometry import Point

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)


@event.listens_for(City, "before_insert")
def set_location_before_insert(mapper, connection, target):
    if target.latitude is not None and target.longitude is not None:
        target.location = from_shape(Point(target.longitude, target.latitude), srid=4326)

@event.listens_for(City, "before_update")
def set_location_before_update(mapper, connection, target):
    if target.latitude is not None and target.longitude is not None:
        target.location = from_shape(Point(target.longitude, target.latitude), srid=4326)

