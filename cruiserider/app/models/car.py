"""
Database Models - Car Database with Prices
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class CarBrand(Base):
    __tablename__ = "car_brands"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)    # "Mahindra"
    slug = Column(String(120), unique=True, nullable=False)    # "mahindra"
    logo_url = Column(String(500))
    country_of_origin = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class CarModel(Base):
    __tablename__ = "car_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id = Column(String, nullable=False)
    brand_name = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)                  # "Thar Roxx"
    slug = Column(String(200), unique=True, nullable=False)    # "mahindra-thar-roxx"
    year = Column(Integer, nullable=False)
    body_type = Column(String(50))        # SUV, Sedan, Hatchback, MUV, Coupe
    fuel_types = Column(JSON, default=list)  # ["Petrol", "Diesel", "Electric"]
    transmission_types = Column(JSON, default=list)  # ["Manual", "Automatic"]
    
    # Key specs for listing cards
    engine_displacement = Column(String(50))   # "2.0L"
    max_power = Column(String(50))             # "160 bhp"
    max_torque = Column(String(50))            # "320 Nm"
    mileage_kmpl = Column(Float)
    seating_capacity = Column(Integer)
    
    # Pricing
    ex_showroom_price_min = Column(Float)      # Starting ex-showroom (lakhs)
    ex_showroom_price_max = Column(Float)      # Top variant ex-showroom (lakhs)
    
    # City-wise on-road prices stored as JSON
    # Format: {"Delhi": {"base": 15.5, "top": 22.3}, "Mumbai": {...}}
    on_road_prices = Column(JSON, default=dict)
    
    # Media
    images = Column(JSON, default=list)        # List of image URLs
    colors = Column(JSON, default=list)        # Available colors
    
    # SEO & Content
    description = Column(Text)
    pros = Column(JSON, default=list)
    cons = Column(JSON, default=list)
    
    # Meta
    cardekho_id = Column(String(100))          # External API reference
    carwale_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CarVariant(Base):
    __tablename__ = "car_variants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    car_model_id = Column(String, nullable=False)
    name = Column(String(200), nullable=False)   # "XUV 3XO MX1 Pro"
    fuel_type = Column(String(50))               # Petrol / Diesel / Electric / CNG
    transmission = Column(String(50))            # Manual / Automatic / DCT / CVT
    ex_showroom_price = Column(Float)            # In lakhs
    # City-wise on-road: {"Delhi": 18.5, "Mumbai": 19.2, "Bangalore": 19.8}
    on_road_prices = Column(JSON, default=dict)
    key_features = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
