from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float, Table
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.accomodation_services.schema import AccomodationCategoryEnum


accomodation_service_images = Table(
    "accomodation_service_images",
    Base.metadata,
    Column("accomodation_service_id", Integer, ForeignKey("accomodation_services.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)


class AccomodationService(Base):
    __tablename__ = 'accomodation_services'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    full_address = Column(String, nullable=False)
    accomodation_category = Column(Enum(AccomodationCategoryEnum, name="accomodationcategoryenum"), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    cost_per_night = Column(Float, nullable=False)

    images = relationship("Image", secondary=accomodation_service_images, uselist=True)