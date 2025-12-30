"""
New Car Market Analyzer

Analyzes Autocosmos catalog data to produce market insights:
- Price distribution by brand, segment, body type
- Model counts and availability
- Price bucket analysis
"""
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from statistics import mean, median
from typing import Optional

from ..config import get_config
from ..models import PriceBucket, VehicleType, get_price_bucket

logger = logging.getLogger(__name__)


@dataclass
class BrandStats:
    """Statistics for a brand"""
    brand: str
    model_count: int
    min_price: Decimal
    max_price: Decimal
    avg_price: Decimal
    median_price: Decimal
    price_range: str  # e.g., "$280k - $1.2M"
    body_types: list
    has_ev: bool
    has_hybrid: bool


@dataclass
class SegmentStats:
    """Statistics for a price segment"""
    segment: str
    segment_label: str
    model_count: int
    brand_count: int
    brands: list
    min_price: Decimal
    max_price: Decimal
    avg_price: Decimal
    top_models: list  # [(brand, model, price), ...]


@dataclass
class BodyTypeStats:
    """Statistics for a body type"""
    body_type: str
    model_count: int
    brand_count: int
    min_price: Decimal
    max_price: Decimal
    avg_price: Decimal
    top_brands: list  # [(brand, count), ...]


class NewCarAnalyzer:
    """Analyzer for new car catalog data"""

    PRICE_BUCKET_LABELS = {
        "entry": "Entry Level (<$150k)",
        "economy": "Economy ($150k-$300k)",
        "mid_range": "Mid-Range ($300k-$500k)",
        "premium": "Premium ($500k-$800k)",
        "luxury": "Luxury ($800k-$1.2M)",
        "ultra": "Ultra Luxury (>$1.2M)",
    }

    def __init__(self, catalog_path: Optional[Path] = None):
        self.config = get_config()

        if catalog_path is None:
            # Find most recent catalog
            autocosmos_dir = self.config.raw_data_path / "autocosmos"
            catalogs = sorted(autocosmos_dir.glob("catalog_*.json"), reverse=True)
            if catalogs:
                catalog_path = catalogs[0]
            else:
                raise FileNotFoundError("No catalog files found")

        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self._clean_data()

    def _load_catalog(self) -> list:
        """Load catalog from JSON file"""
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _clean_data(self):
        """Clean and normalize catalog data"""
        for car in self.catalog:
            # Fix brand names that got concatenated
            brand = car.get("brand", "")
            model = car.get("model", "")

            # Common brand name fixes
            brand_fixes = {
                "Chevroletexpress": "Chevrolet",
                "Chevroletcorvette": "Chevrolet",
                "Chevroletaveo": "Chevrolet",
                "Chevroletblazer": "Chevrolet",
                "Chevroletcaptiva": "Chevrolet",
                "Chevroletequinox": "Chevrolet",
                "Chevrolets10": "Chevrolet",
                "Chevroletsilverado": "Chevrolet",
                "Chevroletspark": "Chevrolet",
                "Chevrolettornado": "Chevrolet",
                "Toyotacorolla": "Toyota",
                "Toyota4Runner": "Toyota",
                "Toyotacamry": "Toyota",
                "Toyotagr": "Toyota",
                "Toyotahighlander": "Toyota",
                "Toyotarav4": "Toyota",
                "Toyotasequoia": "Toyota",
                "Toyotasienna": "Toyota",
                "Toyotatacoma": "Toyota",
                "Toyotatundra": "Toyota",
                "Toyotayaris": "Toyota",
                "Hyundaigrand": "Hyundai",
                "Hyundaisanta": "Hyundai",
                "Hyundaicreta": "Hyundai",
                "Hyundaielantra": "Hyundai",
                "Hyundaihb20": "Hyundai",
                "Hyundaiioniq": "Hyundai",
                "Hyundaipalisade": "Hyundai",
                "Hyundaitucson": "Hyundai",
                "Hondaaccord": "Honda",
                "Hondacivic": "Honda",
                "Hondacr-V": "Honda",
                "Kiak4": "Kia",
                "Kiak3": "Kia",
                "Kianiro": "Kia",
                "Kiasportage": "Kia",
                "Mazda3": "Mazda",
                "Mazda2": "Mazda",
                "Nissankicks": "Nissan",
                "Nissanfrontier": "Nissan",
                "Nissanx-Trail": "Nissan",
                "Volkswagencross": "Volkswagen",
                "Volkswagengolf": "Volkswagen",
                "Volkswagenjetta": "Volkswagen",
                "Volkswagenpolo": "Volkswagen",
            }

            if brand in brand_fixes:
                car["brand"] = brand_fixes[brand]

            # Ensure price is Decimal
            if car.get("base_price_mxn"):
                car["base_price_mxn"] = Decimal(str(car["base_price_mxn"]))

            # Assign price bucket
            if car.get("base_price_mxn"):
                bucket = get_price_bucket(car["base_price_mxn"])
                car["price_bucket"] = bucket.value

            # Detect EV/Hybrid from model name
            model_lower = (model or "").lower()
            car["is_ev"] = any(x in model_lower for x in ["ev", "eléctrico", "electric", "e-power"])
            car["is_hybrid"] = any(x in model_lower for x in ["hybrid", "híbrido", "hev", "phev"])

    def get_brand_stats(self) -> list[BrandStats]:
        """Get statistics by brand"""
        brand_data = defaultdict(list)

        for car in self.catalog:
            brand = car.get("brand", "Unknown")
            if car.get("base_price_mxn"):
                brand_data[brand].append(car)

        stats = []
        for brand, cars in sorted(brand_data.items()):
            prices = [float(c["base_price_mxn"]) for c in cars]
            body_types = list(set(c.get("body_type") for c in cars if c.get("body_type")))

            stats.append(BrandStats(
                brand=brand,
                model_count=len(cars),
                min_price=Decimal(str(min(prices))),
                max_price=Decimal(str(max(prices))),
                avg_price=Decimal(str(int(mean(prices)))),
                median_price=Decimal(str(int(median(prices)))),
                price_range=f"${min(prices)/1000:.0f}k - ${max(prices)/1000:.0f}k",
                body_types=body_types,
                has_ev=any(c.get("is_ev") for c in cars),
                has_hybrid=any(c.get("is_hybrid") for c in cars),
            ))

        return sorted(stats, key=lambda x: -x.model_count)

    def get_segment_stats(self) -> list[SegmentStats]:
        """Get statistics by price segment"""
        segment_data = defaultdict(list)

        for car in self.catalog:
            bucket = car.get("price_bucket", "unknown")
            if car.get("base_price_mxn"):
                segment_data[bucket].append(car)

        # Order segments
        segment_order = ["entry", "economy", "mid_range", "premium", "luxury", "ultra"]

        stats = []
        for segment in segment_order:
            cars = segment_data.get(segment, [])
            if not cars:
                continue

            prices = [float(c["base_price_mxn"]) for c in cars]
            brands = list(set(c.get("brand") for c in cars))

            # Top 5 models by price (most expensive)
            top_models = sorted(cars, key=lambda x: -float(x["base_price_mxn"]))[:5]
            top_models_list = [
                (c["brand"], c["model"], f"${float(c['base_price_mxn']):,.0f}")
                for c in top_models
            ]

            stats.append(SegmentStats(
                segment=segment,
                segment_label=self.PRICE_BUCKET_LABELS.get(segment, segment),
                model_count=len(cars),
                brand_count=len(brands),
                brands=sorted(brands),
                min_price=Decimal(str(min(prices))),
                max_price=Decimal(str(max(prices))),
                avg_price=Decimal(str(int(mean(prices)))),
                top_models=top_models_list,
            ))

        return stats

    def get_body_type_stats(self) -> list[BodyTypeStats]:
        """Get statistics by body type"""
        body_data = defaultdict(list)

        for car in self.catalog:
            body_type = car.get("body_type", "unknown")
            if car.get("base_price_mxn"):
                body_data[body_type].append(car)

        stats = []
        for body_type, cars in sorted(body_data.items()):
            prices = [float(c["base_price_mxn"]) for c in cars]

            # Count by brand
            brand_counts = defaultdict(int)
            for c in cars:
                brand_counts[c.get("brand", "Unknown")] += 1

            top_brands = sorted(brand_counts.items(), key=lambda x: -x[1])[:5]

            stats.append(BodyTypeStats(
                body_type=body_type or "Unknown",
                model_count=len(cars),
                brand_count=len(set(c.get("brand") for c in cars)),
                min_price=Decimal(str(min(prices))),
                max_price=Decimal(str(max(prices))),
                avg_price=Decimal(str(int(mean(prices)))),
                top_brands=top_brands,
            ))

        return sorted(stats, key=lambda x: -x.model_count)

    def get_ev_hybrid_stats(self) -> dict:
        """Get EV and hybrid vehicle statistics"""
        evs = [c for c in self.catalog if c.get("is_ev")]
        hybrids = [c for c in self.catalog if c.get("is_hybrid")]
        total = len(self.catalog)

        ev_prices = [float(c["base_price_mxn"]) for c in evs if c.get("base_price_mxn")]
        hybrid_prices = [float(c["base_price_mxn"]) for c in hybrids if c.get("base_price_mxn")]

        return {
            "total_models": total,
            "ev_count": len(evs),
            "ev_pct": len(evs) / total * 100 if total else 0,
            "ev_avg_price": mean(ev_prices) if ev_prices else 0,
            "ev_brands": list(set(c.get("brand") for c in evs)),
            "hybrid_count": len(hybrids),
            "hybrid_pct": len(hybrids) / total * 100 if total else 0,
            "hybrid_avg_price": mean(hybrid_prices) if hybrid_prices else 0,
            "hybrid_brands": list(set(c.get("brand") for c in hybrids)),
        }

    def get_cheapest_by_brand(self, n: int = 3) -> dict:
        """Get cheapest models per brand"""
        brand_models = defaultdict(list)

        for car in self.catalog:
            if car.get("base_price_mxn"):
                brand_models[car.get("brand", "Unknown")].append(car)

        result = {}
        for brand, cars in brand_models.items():
            sorted_cars = sorted(cars, key=lambda x: float(x["base_price_mxn"]))
            result[brand] = [
                {
                    "model": c["model"],
                    "price": f"${float(c['base_price_mxn']):,.0f}",
                    "body_type": c.get("body_type", "N/A"),
                }
                for c in sorted_cars[:n]
            ]

        return result

    def get_summary(self) -> dict:
        """Get overall market summary"""
        prices = [float(c["base_price_mxn"]) for c in self.catalog if c.get("base_price_mxn")]
        brands = list(set(c.get("brand") for c in self.catalog))

        return {
            "catalog_date": self.catalog_path.stem.replace("catalog_", ""),
            "total_models": len(self.catalog),
            "total_brands": len(brands),
            "brands": sorted(brands),
            "price_min": f"${min(prices):,.0f}",
            "price_max": f"${max(prices):,.0f}",
            "price_avg": f"${mean(prices):,.0f}",
            "price_median": f"${median(prices):,.0f}",
        }

    def generate_report(self) -> str:
        """Generate a text report"""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("KAVAK MARKET RESEARCH - NEW CAR ANALYSIS")
        lines.append(f"Report Date: {date.today().isoformat()}")
        lines.append("=" * 70)
        lines.append("")

        # Summary
        summary = self.get_summary()
        lines.append("MARKET OVERVIEW")
        lines.append("-" * 40)
        lines.append(f"Total Models Analyzed: {summary['total_models']}")
        lines.append(f"Total Brands: {summary['total_brands']}")
        lines.append(f"Price Range: {summary['price_min']} - {summary['price_max']} MXN")
        lines.append(f"Average Price: {summary['price_avg']} MXN")
        lines.append(f"Median Price: {summary['price_median']} MXN")
        lines.append("")

        # Brand Analysis
        lines.append("ANALYSIS BY BRAND")
        lines.append("-" * 40)
        lines.append(f"{'Brand':<15} {'Models':>8} {'Min Price':>12} {'Max Price':>12} {'Avg Price':>12}")
        lines.append("-" * 60)

        for stat in self.get_brand_stats():
            ev_tag = " [EV]" if stat.has_ev else ""
            hybrid_tag = " [HYB]" if stat.has_hybrid else ""
            lines.append(
                f"{stat.brand:<15} {stat.model_count:>8} "
                f"${float(stat.min_price)/1000:>9.0f}k "
                f"${float(stat.max_price)/1000:>9.0f}k "
                f"${float(stat.avg_price)/1000:>9.0f}k"
                f"{ev_tag}{hybrid_tag}"
            )
        lines.append("")

        # Segment Analysis
        lines.append("ANALYSIS BY PRICE SEGMENT")
        lines.append("-" * 40)

        for stat in self.get_segment_stats():
            lines.append(f"\n{stat.segment_label}")
            lines.append(f"  Models: {stat.model_count} from {stat.brand_count} brands")
            lines.append(f"  Price Range: ${float(stat.min_price):,.0f} - ${float(stat.max_price):,.0f}")
            lines.append(f"  Brands: {', '.join(stat.brands[:5])}{'...' if len(stat.brands) > 5 else ''}")
            lines.append("  Top Models:")
            for brand, model, price in stat.top_models[:3]:
                lines.append(f"    - {brand} {model}: {price}")
        lines.append("")

        # EV/Hybrid Analysis
        ev_stats = self.get_ev_hybrid_stats()
        lines.append("ELECTRIC & HYBRID VEHICLES")
        lines.append("-" * 40)
        lines.append(f"Electric Vehicles: {ev_stats['ev_count']} models ({ev_stats['ev_pct']:.1f}%)")
        if ev_stats['ev_avg_price']:
            lines.append(f"  Average EV Price: ${ev_stats['ev_avg_price']:,.0f} MXN")
        lines.append(f"  Brands with EVs: {', '.join(ev_stats['ev_brands'])}")
        lines.append("")
        lines.append(f"Hybrid Vehicles: {ev_stats['hybrid_count']} models ({ev_stats['hybrid_pct']:.1f}%)")
        if ev_stats['hybrid_avg_price']:
            lines.append(f"  Average Hybrid Price: ${ev_stats['hybrid_avg_price']:,.0f} MXN")
        lines.append(f"  Brands with Hybrids: {', '.join(ev_stats['hybrid_brands'])}")
        lines.append("")

        # Cheapest Entry Points
        lines.append("CHEAPEST ENTRY POINTS BY BRAND")
        lines.append("-" * 40)
        cheapest = self.get_cheapest_by_brand(2)
        for brand in sorted(cheapest.keys()):
            models = cheapest[brand]
            if models:
                model_str = ", ".join(f"{m['model']} ({m['price']})" for m in models)
                lines.append(f"{brand}: {model_str}")
        lines.append("")

        lines.append("=" * 70)
        lines.append("End of Report")
        lines.append("=" * 70)

        return "\n".join(lines)


def main():
    """Run analysis"""
    logging.basicConfig(level=logging.INFO)

    analyzer = NewCarAnalyzer()
    report = analyzer.generate_report()
    print(report)

    # Save report
    config = get_config()
    output_path = config.output_path / f"new_car_report_{date.today().isoformat()}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
