from sqlalchemy import Column, Integer, String, ForeignKey, Float
from app.database.database import Base
from geoalchemy2 import Geography


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)