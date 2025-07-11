from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class PlanDay(Base):
    __tablename__ = "plan_days"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    
    steps = relationship("PlanDayStep", uselist=True, cascade="all, delete-orphan", order_by="PlanDayStep.index") 
    plan = relationship("Plan", back_populates="days")