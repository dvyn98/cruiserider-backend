"""
Car Data Service - Fetches car models, variants, and on-road prices

APIs to integrate:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. CarDekho Partner API
   - Contact: partners@cardekho.com  
   - Free for content creators / affiliates
   - Provides: models, variants, prices, images, specs
   
2. CarWale API
   - Contact: api@carwale.com
   - Has a publisher API program
   
3. Zigwheels API
   - zigwheels.com/api-program
   
4. VAHAN (Government) - Free
   - apisetu.gov.in → VAHAN for registration data
   
5. Manual fallback - We scrape/maintain prices ourselves
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For MVP (while waiting for API access), we use a seeded local DB.
"""

import httpx
from typing import List, Dict, Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


# ─── CARDEKHO INTEGRATION ──────────────────────────────────────────────────────

async def fetch_all_brands_cardekho() -> List[Dict]:
    """Fetch all car brands from CarDekho API"""
    if not settings.CARDEKHO_API_KEY:
        logger.warning("CarDekho API key not set. Using mock data.")
        return get_mock_brands()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{settings.CARDEKHO_BASE_URL}/brands",
            headers={"Authorization": f"Bearer {settings.CARDEKHO_API_KEY}"},
        )
        resp.raise_for_status()
        return resp.json().get("brands", [])


async def fetch_models_by_brand(brand_slug: str) -> List[Dict]:
    """Fetch all models for a given brand"""
    if not settings.CARDEKHO_API_KEY:
        return get_mock_models(brand_slug)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{settings.CARDEKHO_BASE_URL}/models",
            params={"brand": brand_slug},
            headers={"Authorization": f"Bearer {settings.CARDEKHO_API_KEY}"},
        )
        resp.raise_for_status()
        return resp.json().get("models", [])


async def fetch_on_road_price(
    model_id: str,
    variant_id: str,
    city: str,
) -> Optional[Dict]:
    """
    Fetch on-road price for a specific variant in a city.
    On-road = Ex-showroom + RTO + Insurance + Other charges
    
    These vary by city because:
    - RTO registration rates differ by state
    - Road tax varies (5-12% depending on state)
    - Delhi, Mumbai, Bangalore have different rates
    """
    if not settings.CARDEKHO_API_KEY:
        return get_mock_onroad_price(model_id, city)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{settings.CARDEKHO_BASE_URL}/onroad-price",
            params={"model_id": model_id, "variant_id": variant_id, "city": city},
            headers={"Authorization": f"Bearer {settings.CARDEKHO_API_KEY}"},
        )
        if resp.status_code == 200:
            return resp.json()
        return None


# ─── MOCK DATA (for local development before API approval) ────────────────────

def get_mock_brands() -> List[Dict]:
    """Seed data for development"""
    return [
        {"id": "mahindra", "name": "Mahindra", "slug": "mahindra", "country": "India"},
        {"id": "tata", "name": "Tata", "slug": "tata", "country": "India"},
        {"id": "maruti", "name": "Maruti Suzuki", "slug": "maruti-suzuki", "country": "Japan/India"},
        {"id": "hyundai", "name": "Hyundai", "slug": "hyundai", "country": "South Korea"},
        {"id": "kia", "name": "Kia", "slug": "kia", "country": "South Korea"},
        {"id": "toyota", "name": "Toyota", "slug": "toyota", "country": "Japan"},
        {"id": "honda", "name": "Honda", "slug": "honda", "country": "Japan"},
        {"id": "mgmotor", "name": "MG Motor", "slug": "mg-motor", "country": "UK/China"},
        {"id": "jeep", "name": "Jeep", "slug": "jeep", "country": "USA"},
        {"id": "volkswagen", "name": "Volkswagen", "slug": "volkswagen", "country": "Germany"},
        {"id": "skoda", "name": "Skoda", "slug": "skoda", "country": "Czech Republic"},
        {"id": "renault", "name": "Renault", "slug": "renault", "country": "France"},
    ]


def get_mock_models(brand_slug: str) -> List[Dict]:
    """Mock models for development - popular cars Priyanshu likely reviews"""
    models_db = {
        "mahindra": [
            {
                "id": "mahindra-thar-roxx-2024",
                "name": "Thar Roxx",
                "year": 2024,
                "body_type": "SUV",
                "fuel_types": ["Petrol", "Diesel"],
                "ex_showroom_min": 12.99,
                "ex_showroom_max": 22.49,
                "engine": "2.0L mStallion / 2.2L mHawk",
                "power": "162 bhp / 130 bhp",
                "seating": 5,
            },
            {
                "id": "mahindra-xuv-3xo-2024",
                "name": "XUV 3XO",
                "year": 2024,
                "body_type": "Compact SUV",
                "fuel_types": ["Petrol", "Diesel"],
                "ex_showroom_min": 7.49,
                "ex_showroom_max": 15.49,
                "engine": "1.2L TGDi / 1.5L Diesel",
                "power": "130 bhp / 115 bhp",
                "seating": 5,
            },
            {
                "id": "mahindra-be6-2025",
                "name": "BE 6",
                "year": 2025,
                "body_type": "Electric SUV",
                "fuel_types": ["Electric"],
                "ex_showroom_min": 18.90,
                "ex_showroom_max": 26.90,
                "engine": "Electric",
                "power": "228 bhp / 282 bhp",
                "seating": 5,
            },
        ],
        "tata": [
            {
                "id": "tata-nexon-2024",
                "name": "Nexon",
                "year": 2024,
                "body_type": "Compact SUV",
                "fuel_types": ["Petrol", "Diesel", "Electric"],
                "ex_showroom_min": 8.00,
                "ex_showroom_max": 15.50,
                "engine": "1.2L Turbo / 1.5L Diesel / Electric",
                "power": "120 bhp / 115 bhp / 143 bhp",
                "seating": 5,
            },
            {
                "id": "tata-harrier-2024",
                "name": "Harrier",
                "year": 2024,
                "body_type": "SUV",
                "fuel_types": ["Diesel"],
                "ex_showroom_min": 15.49,
                "ex_showroom_max": 26.44,
                "engine": "2.0L Kryotec",
                "power": "170 bhp",
                "seating": 5,
            },
        ],
    }
    return models_db.get(brand_slug, [])


def get_mock_onroad_price(model_id: str, city: str) -> Dict:
    """Mock on-road price calculation for development"""
    # Rough on-road = ex-showroom * 1.20 to 1.30 depending on city
    multipliers = {
        "Delhi": 1.18,
        "Mumbai": 1.22,
        "Bangalore": 1.20,
        "Chennai": 1.21,
        "Hyderabad": 1.19,
        "Kolkata": 1.20,
        "Pune": 1.21,
        "Ahmedabad": 1.19,
        "Jaipur": 1.18,
        "Lucknow": 1.20,
    }
    multiplier = multipliers.get(city, 1.20)
    return {
        "city": city,
        "note": "Mock data - connect CarDekho API for real prices",
        "components": {
            "ex_showroom": "Varies by variant",
            "rto": "Approx 7-12% of ex-showroom",
            "insurance": "Approx 3-4% of ex-showroom",
            "other_charges": "Approx 10,000 - 25,000",
        },
        "multiplier_applied": multiplier,
    }


# ─── POPULAR CITIES FOR ON-ROAD PRICES ────────────────────────────────────────

MAJOR_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Chandigarh", "Dehradun", "Noida", "Gurugram", "Faridabad",
    "Bhopal", "Indore", "Nagpur", "Surat", "Kochi",
]
