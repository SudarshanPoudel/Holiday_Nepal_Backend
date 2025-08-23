from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class PlanDay(Base):
    __tablename__ = "plan_days"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    next_plan_day_id = Column(Integer, ForeignKey("plan_days.id"), nullable=True)
    title = Column(String, nullable=False)
    
    next_plan_day = relationship("PlanDay", remote_side=[id], foreign_keys=[next_plan_day_id], uselist=False)
    unordered_steps = relationship("PlanDayStep", uselist=True, cascade="all, delete-orphan") 
    plan = relationship("Plan", back_populates="unordered_days")

    @property
    def steps(self):
        step_map = {step.id: step for step in self.unordered_steps}
        next_ids = {step.next_plan_day_step_id for step in self.unordered_steps if step.next_plan_day_step_id}
        head = next((step for step in self.unordered_steps if step.id not in next_ids), None)

        ordered_steps = []
        current = head
        idx = 0
        while current:
            current.index = idx
            ordered_steps.append(current)
            current = step_map.get(current.next_plan_day_step_id)
            idx += 1

        return ordered_steps