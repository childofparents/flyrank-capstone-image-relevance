import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, Enum, JSON, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

Base = declarative_base()

class ImageStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FLAGGED_LOW_CONFIDENCE = "FLAGGED_LOW_CONFIDENCE"
    FAILED = "FAILED"

class ImageRecord(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False, unique=True)
    status = Column(Enum(ImageStatus), default=ImageStatus.PENDING, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tag = relationship("ImageTagRecord", back_populates="image", uselist=False, cascade="all, delete-orphan")

class ImageTagRecord(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    attributes = Column(JSON, nullable=False)  # Stored as list of strings
    caption = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    image = relationship("ImageRecord", back_populates="tag")

class CostLog(Base):
    __tablename__ = "cost_logs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)  # e.g., "vision_classification", "embedding"
    cost = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False)  # "SUCCESS", "FAILED_VALIDATION", "FAILED_API"
    image_id = Column(Integer, ForeignKey("images.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)