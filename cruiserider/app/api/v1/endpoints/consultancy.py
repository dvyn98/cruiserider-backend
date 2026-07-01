"""
Consultancy API - Car buying/selling consultation bookings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.database import get_db
from app.models.consultancy import ConsultancyBooking
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ConsultancyRequest(BaseModel):
    name: str
    email: str
    phone: str
    city: Optional[str] = None
    consultation_type: Optional[str] = "general"
    budget_min: Optional[str] = None
    budget_max: Optional[str] = None
    preferred_car: Optional[str] = None
    message: Optional[str] = None
    preferred_contact_method: Optional[str] = "whatsapp"
    preferred_time_slot: Optional[str] = None
    utm_source: Optional[str] = None
    referred_video_id: Optional[str] = None


@router.post("/book")
async def book_consultation(
    request: ConsultancyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a car consultation request.
    Frontend: Contact form on the 'Get Expert Advice' page.
    
    After submission:
    - Saves to DB
    - Sends email notification to Priyanshu
    - Returns confirmation to user
    """
    booking = ConsultancyBooking(
        name=request.name,
        email=request.email,
        phone=request.phone,
        city=request.city,
        consultation_type=request.consultation_type,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        preferred_car=request.preferred_car,
        message=request.message,
        preferred_contact_method=request.preferred_contact_method,
        preferred_time_slot=request.preferred_time_slot,
        utm_source=request.utm_source,
        referred_video_id=request.referred_video_id,
    )
    db.add(booking)
    await db.commit()

    # TODO: Send email notification to Priyanshu
    # await send_consultation_notification(booking)

    logger.info(f"New consultation request from {request.name} ({request.phone})")

    return {
        "success": True,
        "booking_id": booking.id,
        "message": "Your consultation request has been received! Priyanshu will contact you within 24 hours.",
        "contact_method": request.preferred_contact_method,
    }


@router.get("/types")
async def get_consultation_types():
    """Get available consultation types for the booking form dropdown"""
    return {
        "types": [
            {"value": "buy_new", "label": "Buy a New Car", "icon": "🚗"},
            {"value": "buy_used", "label": "Buy a Used Car", "icon": "🔍"},
            {"value": "sell_car", "label": "Sell My Car", "icon": "💰"},
            {"value": "compare_cars", "label": "Compare Cars", "icon": "⚖️"},
            {"value": "loan_advice", "label": "Car Loan Advice", "icon": "🏦"},
            {"value": "insurance", "label": "Insurance Guidance", "icon": "🛡️"},
            {"value": "general", "label": "General Query", "icon": "💬"},
        ]
    }


@router.get("/slots")
async def get_available_slots():
    """Get available time slots for consultation"""
    return {
        "slots": [
            "Weekday Morning (10am - 12pm)",
            "Weekday Afternoon (2pm - 4pm)",
            "Weekday Evening (6pm - 8pm)",
            "Weekend Morning (10am - 12pm)",
            "Weekend Afternoon (2pm - 6pm)",
        ]
    }
