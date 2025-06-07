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
    start_municipality_id = Column(Integer, ForeignKey('municipalities.id'), nullable=False)
    end_municipality_id = Column(Integer, ForeignKey('municipalities.id'), nullable=False)
    route_category = Column(Enum(RouteCategoryEnum), nullable=False)
    distance = Column(Float, nullable=False)
    average_time = Column(Integer, nullable=True)

    start_municipality = relationship("Municipality", foreign_keys=[start_municipality_id])
    end_municipality = relationship("Municipality", foreign_keys=[end_municipality_id])