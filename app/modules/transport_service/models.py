from sqlalchemy import Column, Integer, ForeignKey, Float, Enum, String, Table
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.transport_service.schema import TransportServiceCategoryEnum
from app.modules.transport_route.schema import RouteCategoryEnum


# Association table for many-to-many between transport_services and images
transport_service_images = Table(
    'transport_service_images',
    Base.metadata,
    Column('transport_service_id', Integer, ForeignKey('transport_services.id'), primary_key=True),
    Column('image_id', Integer, ForeignKey('images.id'), primary_key=True),
)


class TransportService(Base):
    __tablename__ = 'transport_services'

    id = Column(Integer, primary_key=True)
    service_provider_id = Column(Integer, ForeignKey('service_providers.id'), nullable=False)
    start_municipality_id = Column(Integer, ForeignKey('municipalities.id'), nullable=False)
    end_municipality_id = Column(Integer, ForeignKey('municipalities.id'), nullable=False)
    description = Column(String, nullable=True)
    route_category = Column(Enum(RouteCategoryEnum), nullable=False)
    transport_category = Column(Enum(TransportServiceCategoryEnum, name="transportcategoryenum"), nullable=False)
    total_distance = Column(Float, nullable=False)
    average_duration = Column(Integer, nullable=True)

    start_municipality = relationship("Municipality", foreign_keys=[start_municipality_id])
    end_municipality = relationship("Municipality", foreign_keys=[end_municipality_id])
    provider = relationship("ServiceProvider")

    images = relationship("Image", secondary=transport_service_images)

    # Existing relationship
    route_segments = relationship(
        'TransportServiceRouteSegment',
        back_populates='service',
        order_by='TransportServiceRouteSegment.index',
        cascade='all, delete-orphan'
    )


class TransportServiceRouteSegment(Base):
    __tablename__ = 'transport_service_route_segments'

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('transport_services.id', ondelete='CASCADE'), nullable=False)
    route_id = Column(Integer, ForeignKey('transport_routes.id'), nullable=False)
    index = Column(Integer, nullable=False)

    service = relationship('TransportService', back_populates='route_segments')
    route = relationship('TransportRoute')
