from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database.database import Base


from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.transport_route.schema import RouteCategoryEnum

class TransportRoute(Base):
    __tablename__ = 'transport_routes'

    id = Column(Integer, primary_key=True)
    start_city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    end_city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    route_category = Column(Enum(RouteCategoryEnum), nullable=False)
    distance = Column(Float, nullable=False)
    average_duration = Column(Float, nullable=True)
    average_cost = Column(Float, nullable=True)

    start_city = relationship("City", foreign_keys=[start_city_id])
    end_city = relationship("City", foreign_keys=[end_city_id])