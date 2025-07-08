from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from app.database.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)    

    city_id = Column(Integer, ForeignKey("cities.id"), index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    image = relationship("Image")
    city = relationship("City")
    plans = relationship("Plan", back_populates="user", uselist=True)
    saved_plans = relationship("Plan", secondary="user_saved_plans", back_populates="saved_by_users")
    plan_ratings = relationship("UserPlanRating", back_populates="user")