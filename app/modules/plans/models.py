from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

from app.database.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    total_cost = Column(Float, nullable=False)
    no_of_days = Column(Integer, nullable=False)
    no_of_people = Column(Integer, nullable=False)
    min_budget = Column(Float, nullable=False)
    max_budget = Column(Float, nullable=True)
    min_travel_distance = Column(Float, nullable=False)
    rating = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    is_private = Column(Boolean, nullable=False, default=True)
    start_municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=False)
    end_municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=False)

    user = relationship("User")
    days = relationship("PlanDay", uselist=True, cascade="all, delete-orphan", order_by="PlanDay.index")