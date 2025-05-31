from sqlalchemy import Column, Integer, String, ForeignKey, Float
from app.database.database import Base


class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)  
    headquarter = Column(String, nullable=True)

    def __repr__(self):
        return f"<District(id={self.id}, name='{self.name}')>"


class Municipality(Base):
    __tablename__ = "municipalities"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True) 
    district_id = Column(Integer, ForeignKey("districts.id"), index=True)  
    longitude = Column(Float, nullable=True) 
    latitude = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Municipality(id={self.id}, name='{self.name}')>"