import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    authenticity_score = Column(Float)
    prediction = Column(String)  # REAL or FAKE
    confidence = Column(Float)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, index=True)
