"""
Data standardization utilities for market research

Handles:
- Brand name normalization
- City/state name mapping
- Vehicle type classification
- Price bucket assignment
"""
import re
from decimal import Decimal
from typing import Optional

from ..config import get_config
from ..models import BrandTier, PriceBucket, VehicleType, get_brand_tier, get_price_bucket


class DataStandardizer:
    """Standardize data across different sources"""

    # Brand name normalization map
    BRAND_ALIASES = {
        # Common variations
        "mercedes": "Mercedes-Benz",
        "mercedes benz": "Mercedes-Benz",
        "vw": "Volkswagen",
        "chevy": "Chevrolet",
        "gm": "Chevrolet",
        "land-rover": "Land Rover",
        "landrover": "Land Rover",
        "aston-martin": "Aston Martin",
        "astonmartin": "Aston Martin",
        "alfa-romeo": "Alfa Romeo",
        "alfaromeo": "Alfa Romeo",
        "rolls-royce": "Rolls-Royce",
        "rollsroyce": "Rolls-Royce",

        # Chinese brands
        "byd": "BYD",
        "gwm": "GWM",
        "great wall": "GWM",
        "jac": "JAC",
        "mg": "MG",
        "changan": "Changan",
        "chirey": "Chirey",
        "geely": "Geely",
        "baic": "BAIC",
        "faw": "FAW",
        "haval": "Haval",

        # Japanese
        "toyota": "Toyota",
        "honda": "Honda",
        "nissan": "Nissan",
        "mazda": "Mazda",
        "mitsubishi": "Mitsubishi",
        "subaru": "Subaru",
        "suzuki": "Suzuki",
        "infiniti": "Infiniti",
        "lexus": "Lexus",
        "acura": "Acura",

        # Korean
        "hyundai": "Hyundai",
        "kia": "Kia",
        "genesis": "Genesis",

        # American
        "ford": "Ford",
        "chevrolet": "Chevrolet",
        "dodge": "Dodge",
        "jeep": "Jeep",
        "ram": "RAM",
        "lincoln": "Lincoln",
        "cadillac": "Cadillac",
        "gmc": "GMC",
        "buick": "Buick",
        "chrysler": "Chrysler",

        # European
        "bmw": "BMW",
        "audi": "Audi",
        "volkswagen": "Volkswagen",
        "porsche": "Porsche",
        "volvo": "Volvo",
        "mini": "MINI",
        "seat": "SEAT",
        "cupra": "Cupra",
        "skoda": "Skoda",
        "peugeot": "Peugeot",
        "renault": "Renault",
        "citroen": "Citroën",
        "fiat": "Fiat",
        "ferrari": "Ferrari",
        "lamborghini": "Lamborghini",
        "maserati": "Maserati",
        "jaguar": "Jaguar",
    }

    # State name normalization
    STATE_ALIASES = {
        "cdmx": "Ciudad de México",
        "ciudad de mexico": "Ciudad de México",
        "df": "Ciudad de México",
        "distrito federal": "Ciudad de México",
        "edomex": "Estado de México",
        "edo. mex.": "Estado de México",
        "estado de mexico": "Estado de México",
        "nl": "Nuevo León",
        "nuevo leon": "Nuevo León",
        "bc": "Baja California",
        "baja california norte": "Baja California",
        "bcs": "Baja California Sur",
        "qroo": "Quintana Roo",
        "q. roo": "Quintana Roo",
        "slp": "San Luis Potosí",
        "san luis potosi": "San Luis Potosí",
        "ags": "Aguascalientes",
    }

    # City to state mapping
    CITY_STATE_MAP = {
        "ciudad de méxico": "Ciudad de México",
        "guadalajara": "Jalisco",
        "monterrey": "Nuevo León",
        "puebla": "Puebla",
        "querétaro": "Querétaro",
        "queretaro": "Querétaro",
        "león": "Guanajuato",
        "leon": "Guanajuato",
        "mérida": "Yucatán",
        "merida": "Yucatán",
        "tijuana": "Baja California",
        "aguascalientes": "Aguascalientes",
        "cancún": "Quintana Roo",
        "cancun": "Quintana Roo",
        "cuernavaca": "Morelos",
        "morelia": "Michoacán",
        "san luis potosí": "San Luis Potosí",
        "toluca": "Estado de México",
        "chihuahua": "Chihuahua",
        "hermosillo": "Sonora",
    }

    # Vehicle type keywords
    VEHICLE_TYPE_KEYWORDS = {
        VehicleType.SEDAN: [
            "sedan", "sedán", "sentra", "versa", "jetta", "civic",
            "corolla", "mazda3", "mazda 3", "aveo", "onix",
        ],
        VehicleType.SUV_COMPACT: [
            "kicks", "hr-v", "hrv", "cx-30", "cx30", "venue", "kona",
            "seltos", "tracker", "t-cross", "tcross", "magnite",
        ],
        VehicleType.SUV_MID: [
            "cr-v", "crv", "rav4", "tiguan", "cx-5", "cx5", "tucson",
            "sportage", "equinox", "escape", "x-trail", "xtrail",
        ],
        VehicleType.SUV_FULL: [
            "pilot", "tahoe", "durango", "expedition", "pathfinder",
            "palisade", "telluride", "4runner", "sequoia",
        ],
        VehicleType.PICKUP: [
            "pickup", "hilux", "ranger", "colorado", "frontier",
            "np300", "tacoma", "f-150", "f150", "silverado", "ram",
        ],
        VehicleType.HATCHBACK: [
            "hatchback", "hatch", "fit", "polo", "mazda2", "mazda 2",
            "rio", "accent", "i10", "march", "note",
        ],
        VehicleType.VAN: [
            "van", "minivan", "sienna", "odyssey", "pacifica",
            "carnival", "transit", "urvan",
        ],
        VehicleType.COUPE: [
            "coupe", "coupé", "mustang", "camaro", "86", "supra",
            "z", "370z", "miata", "mx-5",
        ],
    }

    def __init__(self):
        self.config = get_config()

    def normalize_brand(self, brand: str) -> str:
        """Normalize brand name to standard format"""
        if not brand:
            return ""

        # Clean and lowercase for lookup
        cleaned = brand.strip().lower()
        cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)

        # Check aliases
        if cleaned in self.BRAND_ALIASES:
            return self.BRAND_ALIASES[cleaned]

        # Title case as fallback
        return brand.strip().title()

    def normalize_state(self, state: str) -> str:
        """Normalize state name"""
        if not state:
            return ""

        cleaned = state.strip().lower()

        if cleaned in self.STATE_ALIASES:
            return self.STATE_ALIASES[cleaned]

        return state.strip().title()

    def get_state_for_city(self, city: str) -> Optional[str]:
        """Get state name for a city"""
        if not city:
            return None

        cleaned = city.strip().lower()

        if cleaned in self.CITY_STATE_MAP:
            return self.CITY_STATE_MAP[cleaned]

        return None

    def classify_vehicle_type(
        self,
        model_name: str,
        body_type_hint: Optional[str] = None
    ) -> Optional[VehicleType]:
        """
        Classify vehicle type based on model name and hints

        Args:
            model_name: Model name to classify
            body_type_hint: Optional hint from data source

        Returns:
            VehicleType or None if unknown
        """
        if not model_name:
            return None

        model_lower = model_name.lower()

        # Check hint first
        if body_type_hint:
            hint_lower = body_type_hint.lower()
            for vtype, keywords in self.VEHICLE_TYPE_KEYWORDS.items():
                if hint_lower in keywords or any(k in hint_lower for k in keywords):
                    return vtype

        # Check model name
        for vtype, keywords in self.VEHICLE_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in model_lower:
                    return vtype

        return None

    def assign_price_bucket(self, price_mxn: Decimal) -> PriceBucket:
        """Assign price bucket based on price"""
        return get_price_bucket(price_mxn)

    def assign_brand_tier(self, brand: str) -> BrandTier:
        """Assign brand tier"""
        normalized = self.normalize_brand(brand)
        return get_brand_tier(normalized)

    def standardize_record(self, record: dict) -> dict:
        """
        Standardize a data record in-place

        Args:
            record: Dictionary with raw data

        Returns:
            Standardized record
        """
        # Normalize brand
        if "brand" in record:
            record["brand"] = self.normalize_brand(record["brand"])
            record["brand_tier"] = self.assign_brand_tier(record["brand"]).value

        # Normalize state
        if "state" in record:
            record["state"] = self.normalize_state(record["state"])

        # Infer state from city
        if "city" in record and "state" not in record:
            record["state"] = self.get_state_for_city(record["city"])

        # Classify vehicle type
        if "model" in record and "body_type" not in record:
            vtype = self.classify_vehicle_type(
                record["model"],
                record.get("body_type_hint")
            )
            if vtype:
                record["body_type"] = vtype.value

        # Assign price bucket
        if "price_mxn" in record or "list_price_mxn" in record:
            price = record.get("price_mxn") or record.get("list_price_mxn")
            if price:
                record["price_bucket"] = self.assign_price_bucket(Decimal(str(price))).value

        return record


# Global instance
_standardizer = None


def get_standardizer() -> DataStandardizer:
    """Get global standardizer instance"""
    global _standardizer
    if _standardizer is None:
        _standardizer = DataStandardizer()
    return _standardizer
