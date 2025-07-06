from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum, Table
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.plan_day_steps.schema import PlanDayTimeFrameEnum, PlanDayStepCategoryEnum
from app.modules.plan_route_hops.models import PlanRouteHop


plan_day_step_activities = Table(
    "plan_day_step_activities",
    Base.metadata,
    Column("plan_day_step_id", Integer, ForeignKey("plan_day_steps.id"), primary_key=True),
    Column("activity_id", Integer, ForeignKey("activities.id"), primary_key=True),
)

class PlanDayStep(Base):
    __tablename__ = "plan_day_steps"
    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, nullable=False)
    plan_day_id = Column(Integer, ForeignKey("plan_days.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(Enum(PlanDayStepCategoryEnum, name="plandaystepcategoryenum"), nullable=True)
    time_frame = Column(Enum(PlanDayTimeFrameEnum, name="plandaytimeframeenum"), nullable=False)
    duration = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=True)
    place_activity_id = Column(Integer, ForeignKey("place_activities.id"), nullable=True)
    start_municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=True)
    end_municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=True)

    image = relationship("Image")
    place = relationship("Place")
    activities = relationship("Activity", secondary=plan_day_step_activities)
    municipality_start = relationship("Municipality", foreign_keys=[start_municipality_id])
    municipality_end = relationship("Municipality", foreign_keys=[end_municipality_id])
    route_hops = relationship("PlanRouteHop", back_populates="plan_day_step", uselist=True, cascade="all, delete-orphan")