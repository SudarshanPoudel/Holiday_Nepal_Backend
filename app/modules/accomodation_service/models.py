from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float, Table
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.accomodation_service.schema import AccomodationCategoryEnum


accomodation_service_images = Table(
    "accomodation_service_images",
    Base.metadata,
    Column("accomodation_service_id", Integer, ForeignKey("accomodation_services.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)


class AccomodationService(Base):
    __tablename__ = 'accomodation_services'

    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=True)
    service_provider_id = Column(Integer, ForeignKey('service_providers.id'), nullable=True)
    municipality_id = Column(Integer, ForeignKey('municipalities.id'), nullable=False)
    full_location = Column(String, nullable=False)
    accomodation_category = Column(Enum(AccomodationCategoryEnum, name="accomodationcategoryenum"), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    cost_per_night = Column(Float, nullable=False)

    images = relationship("Image", secondary=accomodation_service_images)