from sqlalchemy import Column, Integer, String, ForeignKey, Float
from app.database.database import Base


class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)  

    def __repr__(self):
        return f"<District(id={self.id}, name='{self.name}')>"


class Municipality(Base):
    __tablename__ = "municipalities"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True) 
    district_id = Column(Integer, ForeignKey("districts.id"), index=True)  
    wards = Column(Integer)

    def __repr__(self):
        return f"<Municipality(id={self.id}, name='{self.name}', district_id={self.district_id})>"


class Ward(Base):
    __tablename__ = "wards"
    id = Column(Integer, primary_key=True)
    number = Column(Integer)  
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), index=True) 
    longitude = Column(Float) 
    latitude = Column(Float)

    def __repr__(self):
        return f"<Ward(id={self.id}, number={self.number}, municipality_id={self.municipality_id})>"
