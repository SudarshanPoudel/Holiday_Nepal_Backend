from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from app.database.database import Base
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    profile_picture_key = Column(String, nullable=True)
    
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), index=True)

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"