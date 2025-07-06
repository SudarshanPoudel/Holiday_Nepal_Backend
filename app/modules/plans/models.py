from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

from app.database.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    no_of_days = Column(Integer, nullable=False)
    no_of_people = Column(Integer, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    rating = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    is_private = Column(Boolean, nullable=False, default=True)
    start_city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    
    user = relationship("User")
    days = relationship("PlanDay", uselist=True, cascade="all, delete-orphan", order_by="PlanDay.index")