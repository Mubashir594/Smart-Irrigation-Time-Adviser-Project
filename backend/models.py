from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=True, default="")
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    history = relationship("IrrigationHistory", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

class IrrigationHistory(Base):
    __tablename__ = "irrigation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_type = Column(String(50), nullable=False)
    soil_type = Column(String(50), nullable=False)
    weather_condition = Column(String(50), nullable=False)
    hours_since_irrigation = Column(Integer, nullable=False)
    eto_estimate = Column(Float, nullable=False, default=4.8)
    crop_coefficient = Column(Float, nullable=False, default=1.0)
    etc_loss_rate = Column(Float, nullable=False)
    estimated_moisture = Column(Float, nullable=False)
    estimated_time_to_critical_deficit = Column(Float, nullable=False)
    irrigation_status = Column(String(100), nullable=False)
    recommendation = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="history")

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    sensor_frequency = Column(String(50), default="Standard (15m)", nullable=False)
    autonomous_mode = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="settings")
