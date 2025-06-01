from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.database import Base


class PlaceActivity(Base):
    __tablename__ = "place_activities"

    id = Column(Integer, primary_key=True)
    place_id = Column(Integer, ForeignKey("places.id"), index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), index=True)
    description = Column(String, nullable=True)

    average_duration = Column(Integer, nullable=True)
    average_cost = Column(Float, nullable=True)

    place = relationship("Place", back_populates="place_activities")
    activity = relationship("Activity", back_populates="place_activities")
