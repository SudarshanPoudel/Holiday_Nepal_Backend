from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float
from app.core.config import settings
from app.database.database import Base
from app.modules.storage.schema import ImageCategoryEnum

def generate_url_from_key(key: str) -> str:
    return f"http://localhost:4566/{settings.bucket_name}/{key}"

class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    category = Column(Enum(ImageCategoryEnum), nullable=True)

    @property
    def url(self) -> str:
        return generate_url_from_key(self.key) 
    