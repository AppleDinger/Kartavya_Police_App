from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from .database import Base

DEFAULT_PHOTO = "https://cdn-icons-png.flaticon.com/512/847/847969.png"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_known_lat = Column(Float, nullable=True)
    last_known_long = Column(Float, nullable=True)
    leave_requested = Column(Boolean, default=False)
    is_on_leave = Column(Boolean, default=False)
    profile_photo = Column(String, default=DEFAULT_PHOTO)
    
    # NEW: Ping Preference
    pings_enabled = Column(Boolean, default=True)

    deployments = relationship("Deployment", back_populates="officer")
    subordinates = relationship("User", backref=backref("supervisor", remote_side=[id]), foreign_keys=[supervisor_id])

class Deployment(Base):
    __tablename__ = "deployments"
    id = Column(Integer, primary_key=True, index=True)
    officer_id = Column(Integer, ForeignKey("users.id"))
    target_lat = Column(Float)
    target_long = Column(Float)
    radius_meters = Column(Float)
    current_lat = Column(Float, nullable=True)
    current_long = Column(Float, nullable=True)
    last_checkin = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    status = Column(String, default="deployed") 
    officer = relationship("User", back_populates="deployments")

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String) 
    message = Column(String)
    # Optional: Link to specific user for filtering officer logs
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

# NEW: Ping System
class Ping(Base):
    __tablename__ = "pings"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    lat = Column(Float)
    long = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True) # Active until clicked/dismissed