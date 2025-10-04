from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.sql import func
from ..database.connection import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(255))
    operation = Column(String(255))
    price = Column(Float)
    rooms = Column(Integer)
    bathrooms = Column(Integer)
    surface = Column(Float)
    title = Column(Text)
    location = Column(String(255))
    address = Column(Text)
    url = Column(Text)  # Removido unique=True para permitir múltiples registros con timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    website = Column(String(255))
    scraping_date = Column(DateTime(timezone=True), server_default=func.now())  # Nueva columna para tracking

    # Índice compuesto para mejorar consultas por URL y fecha
    __table_args__ = (Index('idx_url_scraping_date', 'url', 'scraping_date'),)

    def __repr__(self):
        return f"<Property(reference='{self.reference}', title='{self.title}', scraping_date='{self.scraping_date}')>"