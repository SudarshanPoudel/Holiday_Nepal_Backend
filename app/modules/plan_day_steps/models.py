from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum, Table
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.plan_day_steps.schema import PlanDayTimeFrameEnum, PlanDayStepCategoryEnum


plan_day_step_activities = Table(
    "plan_day_step_activities",
    Base.metadata,
    Column("plan_day_step_id", Integer, ForeignKey("plan_day_steps.id"), primary_key=True),
    Column("activity_id", Integer, ForeignKey("activities.id"), primary_key=True),
)

class PlanDayStep(Base):
    __tablename__ = "plan_day_steps"
    id = Column(Integer, primary_key=True, index=True)
    plan_day_id = Column(Integer, ForeignKey("plan_days.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(Enum(PlanDayStepCategoryEnum, name="plandaystepcategoryenum"), nullable=True)
    time_frame = Column(Enum(PlanDayTimeFrameEnum, name="plandaytimeframeenum"), nullable=False)
    duration = Column(Float, nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=True)
    municipality_start_id = Column(Integer, ForeignKey("municipalities.id"), nullable=True)
    municipality_end_id = Column(Integer, ForeignKey("municipalities.id"), nullable=True)

    image = relationship("Image")
    place = relationship("Place")
    activities = relationship("Activity", secondary=plan_day_step_activities)
    municipality_start = relationship("Municipality", foreign_keys=[municipality_start_id])
    municipality_end = relationship("Municipality", foreign_keys=[municipality_end_id])