"""
Data models for KAVAK Market Research
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional


class VehicleType(str, Enum):
    SEDAN = "sedan"
    SUV_COMPACT = "suv_compact"
    SUV_MID = "suv_mid"
    SUV_FULL = "suv_full"
    PICKUP = "pickup"
    HATCHBACK = "hatchback"
    VAN = "van"
    COUPE = "coupe"


class FuelType(str, Enum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    ELECTRIC = "electric"


class Transmission(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"


class BrandTier(str, Enum):
    VOLUME = "volume"
    PREMIUM = "premium"
    LUXURY = "luxury"


class PriceBucket(str, Enum):
    ENTRY = "entry"          # < 150k
    ECONOMY = "economy"      # 150-300k
    MID_RANGE = "mid_range"  # 300-500k
    PREMIUM = "premium"      # 500-800k
    LUXURY = "luxury"        # 800k-1.2M
    ULTRA = "ultra"          # > 1.2M


@dataclass
class City:
    """City configuration"""
    code: str
    name: str
    state: str
    tier: int = 1


@dataclass
class NewCarModel:
    """New car model with MSRP pricing from Autocosmos"""
    brand: str
    model: str
    year: int
    body_type: Optional[VehicleType] = None
    base_price_mxn: Optional[Decimal] = None
    versions: list = field(default_factory=list)
    engine: Optional[str] = None
    transmission: Optional[Transmission] = None
    fuel_type: Optional[FuelType] = None
    origin_country: Optional[str] = None
    source: str = "autocosmos"
    scraped_date: Optional[date] = None


@dataclass
class NewCarVersion:
    """Specific version/trim of a new car"""
    name: str
    price_mxn: Decimal
    engine: Optional[str] = None
    horsepower: Optional[int] = None
    transmission: Optional[Transmission] = None
    fuel_type: Optional[FuelType] = None


@dataclass
class INEGIProductionData:
    """INEGI monthly production/sales data"""
    period: str  # YYYY-MM format
    brand: str
    model: Optional[str] = None
    production_units: int = 0
    domestic_sales_units: int = 0
    export_units: int = 0
    source: str = "inegi_raiavl"


@dataclass
class INEGIRegistrationData:
    """INEGI vehicle registration data by state"""
    period: str  # YYYY-MM format
    state: str
    state_code: str
    vehicle_class: str  # automovil, camion, motocicleta
    service_type: str   # particular, publico, oficial
    total_registered: int = 0
    source: str = "inegi_vmrc"


@dataclass
class UsedCarListing:
    """KAVAK used car listing"""
    internal_id: str
    brand: str
    model: str
    year: int
    body_type: Optional[VehicleType] = None
    transmission: Optional[Transmission] = None
    fuel_type: Optional[FuelType] = None
    mileage_km: int = 0
    color: Optional[str] = None
    trim: Optional[str] = None

    # Location
    city: Optional[str] = None
    state: Optional[str] = None
    hub_id: Optional[str] = None

    # Pricing
    list_price_mxn: Optional[Decimal] = None
    purchase_price_mxn: Optional[Decimal] = None

    # Timing
    acquisition_date: Optional[date] = None
    listing_date: Optional[date] = None
    sold_date: Optional[date] = None
    days_in_inventory: int = 0

    # Demand metrics
    page_views: int = 0
    leads_generated: int = 0

    # Status
    status: str = "available"  # available, reserved, sold, in_transit


@dataclass
class MarketMetrics:
    """Aggregated market metrics for a dimension"""
    period: str
    dimension_type: str  # city, brand, body_type, price_bucket
    dimension_value: str

    # Volume metrics
    new_car_sales: int = 0
    used_car_sales: int = 0
    total_inventory: int = 0

    # Price metrics
    avg_new_car_price: Optional[Decimal] = None
    avg_used_car_price: Optional[Decimal] = None
    median_used_car_price: Optional[Decimal] = None

    # Performance metrics
    avg_days_to_sale: Optional[float] = None
    inventory_turnover: Optional[float] = None

    # Comparisons
    mom_change_pct: Optional[float] = None
    yoy_change_pct: Optional[float] = None


def get_price_bucket(price_mxn: Decimal) -> PriceBucket:
    """Determine price bucket from price"""
    price = float(price_mxn)
    if price < 150_000:
        return PriceBucket.ENTRY
    elif price < 300_000:
        return PriceBucket.ECONOMY
    elif price < 500_000:
        return PriceBucket.MID_RANGE
    elif price < 800_000:
        return PriceBucket.PREMIUM
    elif price < 1_200_000:
        return PriceBucket.LUXURY
    else:
        return PriceBucket.ULTRA


def get_brand_tier(brand: str) -> BrandTier:
    """Determine brand tier from brand name"""
    brand_upper = brand.upper()

    luxury_brands = {
        "PORSCHE", "LAND ROVER", "LEXUS", "JAGUAR", "MASERATI",
        "FERRARI", "LAMBORGHINI", "BENTLEY", "ASTON MARTIN", "ROLLS-ROYCE"
    }

    premium_brands = {
        "BMW", "MERCEDES-BENZ", "MERCEDES", "AUDI", "VOLVO", "MINI",
        "ACURA", "INFINITI", "LINCOLN", "CADILLAC", "GENESIS"
    }

    if brand_upper in luxury_brands:
        return BrandTier.LUXURY
    elif brand_upper in premium_brands:
        return BrandTier.PREMIUM
    else:
        return BrandTier.VOLUME
