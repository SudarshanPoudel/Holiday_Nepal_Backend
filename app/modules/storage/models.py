from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float

from app.database.database import Base
from app.modules.storage.schema import ImageCategoryEnum


class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    url = Column(String, nullable=True) 
    category = Column(Enum(ImageCategoryEnum), nullable=True)