from sqlalchemy import CheckConstraint, Column, Integer, String, ForeignKey, Float, Boolean, Table, func, DateTime
from sqlalchemy.orm import relationship

from app.database.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    no_of_days = Column(Integer, nullable=False)
    no_of_people = Column(Integer, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    rating = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    is_private = Column(Boolean, nullable=False, default=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    start_city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, onupdate=func.now(), server_default=func.now())
    
    user = relationship("User")
    image = relationship("Image")
    unordered_days = relationship("PlanDay", uselist=True, cascade="all, delete-orphan")
    start_city = relationship("City", foreign_keys=[start_city_id])
    saved_by_users = relationship("User", secondary="user_saved_plans", back_populates="saved_plans")

    @property
    def days(self):
        days_map = {day.id: day for day in self.unordered_days}
        next_ids = {day.next_plan_day_id for day in self.unordered_days if day.next_plan_day_id}
        head = next((day for day in self.unordered_days if day.id not in next_ids), None)
        ordered_days = []
        current = head
        idx = 0
        while current:
            current.index = idx
            ordered_days.append(current)
            current = days_map.get(current.next_plan_day_id)
            idx += 1

        return ordered_days


user_saved_plans = Table(
    "user_saved_plans",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("plan_id", Integer, ForeignKey("plans.id"), primary_key=True),
)

class UserPlanRating(Base):
    __tablename__ = "user_plan_ratings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    rating = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_between_1_and_5'),
    )

    user = relationship("User")
    plan = relationship("Plan")