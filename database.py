from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

from config import settings

# Configure engine based on environment
if settings.ENVIRONMENT == "production":
    # Production configuration with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300
    )
else:
    # Development configuration
    engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'crm', 'salesperson', 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Salesperson specific fields
    phone = Column(String)
    designation = Column(String)
    photo_url = Column(String)
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    last_location_update = Column(DateTime)
    status = Column(String, default="available")  # 'available', 'busy'
    territory = Column(String)  # Territory/State assignment
    
    # Relationships
    assignments = relationship("Assignment", back_populates="salesperson", foreign_keys="Assignment.salesperson_id")

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_person = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="unassigned")  # 'unassigned', 'assigned', 'contacted', 'closed'
    priority = Column(String, default="warm")  # 'hot', 'warm', 'cold'
    estimated_value = Column(Float)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    assignments = relationship("Assignment", back_populates="lead")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    salesperson_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime, default=func.now())
    status = Column(String, default="pending")  # 'pending', 'accepted', 'completed', 'rejected'
    notes = Column(Text)
    
    # Relationships
    lead = relationship("Lead", back_populates="assignments")
    salesperson = relationship("User", back_populates="assignments", foreign_keys=[salesperson_id])

class PreLead(Base):
    __tablename__ = "pre_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    reason = Column(Text, nullable=False)  # Reason for prospecting
    source = Column(String, nullable=False)  # Source of the lead (referral, cold call, etc.)
    classification = Column(String, default="warm")  # 'hot', 'warm', 'cold'
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    converted_to_lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)  # Track if converted
    converted_at = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    converted_lead = relationship("Lead", foreign_keys=[converted_to_lead_id])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
