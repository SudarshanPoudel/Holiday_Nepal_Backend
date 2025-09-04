from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float, Table
from app.database.types import EnumList
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.modules.places.schema import PlaceCategoryEnum

place_images = Table(
    "place_images",
    Base.metadata,
    Column("place_id", Integer, ForeignKey("places.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    categories= Column(EnumList(PlaceCategoryEnum), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    average_visit_duration = Column(Float, nullable=True)
    average_visit_cost = Column(Float, nullable=True)
    embedding = Column(Vector(384), nullable=True)

    place_activities = relationship("PlaceActivity", back_populates="place", cascade="all, delete-orphan", uselist=True)
    images = relationship("Image", secondary=place_images, uselist=True)
    city = relationship("City", foreign_keys=[city_id])