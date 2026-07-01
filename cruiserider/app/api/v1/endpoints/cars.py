"""
Cars API - Car database, variants, and on-road prices
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional, List
from app.core.database import get_db
from app.models.car import CarBrand, CarModel, CarVariant
from app.services.car_service import MAJOR_CITIES, get_mock_brands, get_mock_models
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/brands")
async def get_brands(db: AsyncSession = Depends(get_db)):
    """
    Get all car brands.
    Frontend: Used for brand filter dropdowns.
    """
    result = await db.execute(
        select(CarBrand).where(CarBrand.is_active == True).order_by(CarBrand.name)
    )
    brands = result.scalars().all()

    if not brands:
        # Return mock data during development before DB is seeded
        return get_mock_brands()

    return [
        {
            "id": b.id,
            "name": b.name,
            "slug": b.slug,
            "logo_url": b.logo_url,
        }
        for b in brands
    ]


@router.get("/models")
async def get_car_models(
    brand_slug: Optional[str] = None,
    body_type: Optional[str] = None,
    fuel_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get car models with filtering.
    Frontend: Main car listing page (like CarDekho's model grid).
    """
    query = select(CarModel).where(CarModel.is_active == True)

    if brand_slug:
        query = query.where(CarModel.brand_name.ilike(brand_slug))
    if body_type:
        query = query.where(CarModel.body_type.ilike(f"%{body_type}%"))
    if min_price:
        query = query.where(CarModel.ex_showroom_price_min >= min_price)
    if max_price:
        query = query.where(CarModel.ex_showroom_price_max <= max_price)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    query = query.order_by(CarModel.brand_name, CarModel.name)
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    models = result.scalars().all()

    if not models and brand_slug:
        # Return mock data for dev
        return {"total": 0, "models": get_mock_models(brand_slug)}

    return {
        "total": total,
        "page": page,
        "models": [model_to_dict(m) for m in models],
    }


@router.get("/models/{slug}")
async def get_car_model_detail(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Get full car model details including all variants and prices.
    Frontend: Car detail page.
    """
    result = await db.execute(
        select(CarModel).where(CarModel.slug == slug, CarModel.is_active == True)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Car model not found")

    # Get all variants
    variants_result = await db.execute(
        select(CarVariant).where(
            CarVariant.car_model_id == model.id, CarVariant.is_active == True
        )
    )
    variants = variants_result.scalars().all()

    return {
        **model_to_dict(model),
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "fuel_type": v.fuel_type,
                "transmission": v.transmission,
                "ex_showroom_price": v.ex_showroom_price,
                "on_road_prices": v.on_road_prices or {},
                "key_features": v.key_features or [],
            }
            for v in variants
        ],
    }


@router.get("/models/{slug}/onroad-price")
async def get_onroad_price(
    slug: str,
    city: str = Query(..., description=f"City name. Options: {', '.join(MAJOR_CITIES[:5])}..."),
    db: AsyncSession = Depends(get_db),
):
    """
    Get on-road price for a car in a specific city.
    On-road = Ex-showroom + RTO + Insurance + Other charges.
    This varies by city due to different state taxes.
    
    Frontend: Price calculator widget on car detail pages.
    """
    result = await db.execute(
        select(CarModel).where(CarModel.slug == slug)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Car not found")

    city_prices = (model.on_road_prices or {}).get(city)

    if not city_prices:
        return {
            "car": model.name,
            "city": city,
            "message": "On-road price not yet available for this city. Contact us for exact quote.",
            "available_cities": list((model.on_road_prices or {}).keys()),
            "all_cities": MAJOR_CITIES,
        }

    return {
        "car": model.name,
        "brand": model.brand_name,
        "city": city,
        "on_road_prices": city_prices,
        "ex_showroom_range": {
            "min": model.ex_showroom_price_min,
            "max": model.ex_showroom_price_max,
        },
    }


@router.get("/cities")
async def get_cities():
    """Get list of supported cities for on-road price lookup"""
    return {"cities": MAJOR_CITIES}


@router.get("/compare")
async def compare_cars(
    slugs: str = Query(..., description="Comma-separated car slugs. E.g. mahindra-thar-roxx,tata-harrier"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare up to 3 cars side by side.
    Frontend: Car comparison page.
    """
    slug_list = [s.strip() for s in slugs.split(",")][:3]  # Max 3
    cars = []

    for slug in slug_list:
        result = await db.execute(select(CarModel).where(CarModel.slug == slug))
        car = result.scalar_one_or_none()
        if car:
            cars.append(model_to_dict(car))

    return {"cars": cars, "count": len(cars)}


def model_to_dict(m: CarModel) -> dict:
    return {
        "id": m.id,
        "brand": m.brand_name,
        "name": m.name,
        "slug": m.slug,
        "year": m.year,
        "body_type": m.body_type,
        "fuel_types": m.fuel_types or [],
        "transmission_types": m.transmission_types or [],
        "engine_displacement": m.engine_displacement,
        "max_power": m.max_power,
        "max_torque": m.max_torque,
        "mileage_kmpl": m.mileage_kmpl,
        "seating_capacity": m.seating_capacity,
        "ex_showroom_min": m.ex_showroom_price_min,
        "ex_showroom_max": m.ex_showroom_price_max,
        "images": m.images or [],
        "colors": m.colors or [],
        "description": m.description,
        "pros": m.pros or [],
        "cons": m.cons or [],
        "is_featured": m.is_featured,
    }
