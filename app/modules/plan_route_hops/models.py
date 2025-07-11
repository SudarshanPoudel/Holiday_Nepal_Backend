from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database.database import Base


class PlanRouteHop(Base):
    __tablename__ = "plan_route_hops"

    id = Column(Integer, primary_key=True, index=True)
    plan_day_step_id = Column(Integer, ForeignKey("plan_day_steps.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(Integer, ForeignKey("transport_routes.id"), nullable=False)
    index = Column(Integer, nullable=False)
    destination_city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    
    route = relationship("TransportRoute")
    plan_day_step = relationship("PlanDayStep", back_populates="route_hops")