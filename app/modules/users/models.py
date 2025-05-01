from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from app.database.database import Base
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    
    district_id = Column(Integer, ForeignKey("districts.id"), index=True)
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), index=True)

    created = Column(DateTime(timezone=True), server_default=func.now())