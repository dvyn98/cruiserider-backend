"""
Database Models - Car Consultancy Bookings
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


class ConsultancyStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConsultancyType(str, enum.Enum):
    BUY_NEW = "buy_new"
    BUY_USED = "buy_used"
    SELL_CAR = "sell_car"
    COMPARE_CARS = "compare_cars"
    LOAN_ADVICE = "loan_advice"
    INSURANCE = "insurance"
    GENERAL = "general"


class ConsultancyBooking(Base):
    __tablename__ = "consultancy_bookings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Customer info
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    city = Column(String(100))
    
    # Consultation details
    consultation_type = Column(String(50), default=ConsultancyType.GENERAL)
    budget_min = Column(String(50))          # "5 Lakh"
    budget_max = Column(String(50))          # "10 Lakh"
    preferred_car = Column(String(200))      # What car they're interested in
    message = Column(Text)                   # Detailed query
    
    # Preferred contact
    preferred_contact_method = Column(String(20), default="whatsapp")  # whatsapp/call/email
    preferred_time_slot = Column(String(100))  # "Weekday Evening 6-8pm"
    
    # Status tracking
    status = Column(String(20), default=ConsultancyStatus.PENDING)
    admin_notes = Column(Text)               # Internal notes for Priyanshu
    
    # UTM / Source tracking
    utm_source = Column(String(100))         # youtube / instagram / organic
    referred_video_id = Column(String(200))  # Which video brought them
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
