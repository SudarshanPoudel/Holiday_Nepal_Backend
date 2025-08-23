from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float, Table
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.accommodation_services.schema import AccomodationCategoryEnum


accommodation_service_images = Table(
    "accommodation_service_images",
    Base.metadata,
    Column("accommodation_service_id", Integer, ForeignKey("accommodation_services.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)


class AccomodationService(Base):
    __tablename__ = 'accommodation_services'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    full_address = Column(String, nullable=False)
    accommodation_category = Column(Enum(AccomodationCategoryEnum, name="accommodationcategoryenum"), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    cost_per_night = Column(Float, nullable=False)

    images = relationship("Image", secondary=accommodation_service_images, uselist=True)
    city = relationship("City", foreign_keys=[city_id])