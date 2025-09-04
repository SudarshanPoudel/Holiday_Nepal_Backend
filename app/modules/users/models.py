from sqlalchemy import Boolean, Column, Enum, Integer, String, ForeignKey, DateTime, Table
from app.database.types import EnumList
from app.modules.places.schema import PlaceCategoryEnum
from app.modules.users.schemas import DistancePreferenceEnum
from app.database.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

user_prefer_place_activities = Table(
    "user_prefer_place_activities",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("activities_id", Integer, ForeignKey("activities.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)    

    city_id = Column(Integer, ForeignKey("cities.id"), index=True, nullable=True)
    prefer_place_categories = Column(EnumList(PlaceCategoryEnum), nullable=True)
    prefer_travel_distance = Column(Enum(DistancePreferenceEnum, name="distancepreferenceenum"), nullable=True)
    additional_preferences = Column(String, nullable=True)

    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    image = relationship("Image")
    city = relationship("City")
    plans = relationship("Plan", back_populates="user", uselist=True)
    saved_plans = relationship("Plan", secondary="user_saved_plans", back_populates="saved_by_users")
    plan_ratings = relationship("UserPlanRating", back_populates="user")
    prefer_activities = relationship("Activity", secondary=user_prefer_place_activities)