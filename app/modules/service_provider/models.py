from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Float, Table, Boolean
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.modules.service_provider.schema import ServiceProviderCategoryEnum


class VerificationDocuments(Base):
    __tablename__ = 'service_provider_documents'

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    key = Column(String, nullable=False)
    service_provider_id = Column(Integer, ForeignKey('service_providers.id'), nullable=False)

    service_provider = relationship("ServiceProvider", back_populates="documents")

class ServiceProvider(Base):
    __tablename__ = 'service_providers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    contact_no = Column(String, nullable=False)
    address = Column(String, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    category = Column(Enum(ServiceProviderCategoryEnum) , nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    documents = relationship("VerificationDocuments", back_populates="service_provider")
    user = relationship("User")