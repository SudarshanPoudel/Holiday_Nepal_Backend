from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float, Table
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.modules.places.schema import PlaceCategoryEnum

place_images = Table(
    "place_images",
    Base.metadata,
    Column("place_id", Integer, ForeignKey("places.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    category= Column(Enum(PlaceCategoryEnum, name="placecategoryenum"), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=False)

    place_activities = relationship("PlaceActivity", back_populates="place", cascade="all, delete-orphan")
    images = relationship("Image", secondary=place_images)
    municipality = relationship("Municipality", foreign_keys=[municipality_id])

    @property
    def activities(self):
        return [pa.activity for pa in self.place_activities]
