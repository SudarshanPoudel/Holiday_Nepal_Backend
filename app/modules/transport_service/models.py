from sqlalchemy import Column, Integer, ForeignKey, Float, Enum, String
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.transport_service.schema import TransportServiceCategoryEnum
from app.modules.transport_route.schema import RouteCategoryEnum


class TransportService(Base):
    __tablename__ = 'transport_services'

    id = Column(Integer, primary_key=True)
    service_provider_id = Column(Integer, ForeignKey('service_providers.id'), nullable=False)
    start_municipality_id = Column(Integer, ForeignKey('municipalities.id'), nullable=False)
    end_municipality_id = Column(Integer, ForeignKey('municipalities.id'), nullable=False)
    image = Column(String, nullable=True)
    description = Column(String, nullable=True)
    route_category = Column(Enum(RouteCategoryEnum), nullable=False)
    transport_category = Column(Enum(TransportServiceCategoryEnum, name="transportcategoryenum"), nullable=False)
    total_distance = Column(Float, nullable=False)
    average_time = Column(Integer, nullable=True)

    route_segments = relationship('TransportServiceRouteSegment', back_populates='service', order_by='TransportServiceRouteSegment.sequence')
    provider = relationship("ServiceProvider")



class TransportServiceRouteSegment(Base):
    __tablename__ = 'transport_service_route_segments'

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('transport_services.id'), nullable=False)
    route_id = Column(Integer, ForeignKey('transport_routes.id'), nullable=False)
    sequence = Column(Integer, nullable=False) 

    service = relationship('TransportService', back_populates='route_segments')
    route = relationship('TransportRoute')
