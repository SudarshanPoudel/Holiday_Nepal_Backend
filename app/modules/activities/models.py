from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)

    place_activities = relationship("PlaceActivity", back_populates="activity", cascade="all, delete-orphan")
    image = relationship("Image")

    @property
    def places(self):
        return [pa.place for pa in self.place_activities]
