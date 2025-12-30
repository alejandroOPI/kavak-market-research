"""
Autocosmos Scraper for new car prices in Mexico

Source: https://www.autocosmos.com.mx/catalogo

Extracts:
- All brands and models available in Mexico
- MSRP prices by version/trim
- Specifications (engine, transmission, body type)
"""
import json
import logging
import re
import time
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Generator, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..config import get_config
from ..models import (
    FuelType,
    NewCarModel,
    NewCarVersion,
    Transmission,
    VehicleType,
)

logger = logging.getLogger(__name__)


class AutocosmosScraper:
    """Scraper for Autocosmos new car catalog"""

    BASE_URL = "https://www.autocosmos.com.mx"
    CATALOG_URL = "https://www.autocosmos.com.mx/catalogo"
    BRANDS_URL = "https://www.autocosmos.com.mx/catalogo/vigente"

    # Rate limiting
    REQUEST_DELAY = 1.0  # seconds between requests

    # Body type mapping from URL segments to our enum
    BODY_TYPE_MAP = {
        "sedan": VehicleType.SEDAN,
        "sedán": VehicleType.SEDAN,
        "suv": VehicleType.SUV_MID,
        "crossover": VehicleType.SUV_COMPACT,
        "pickup": VehicleType.PICKUP,
        "hatchback": VehicleType.HATCHBACK,
        "minivan": VehicleType.VAN,
        "van": VehicleType.VAN,
        "coupe": VehicleType.COUPE,
        "coupé": VehicleType.COUPE,
        "convertible": VehicleType.COUPE,
        "station-wagon": VehicleType.SEDAN,
    }

    # Transmission mapping
    TRANSMISSION_MAP = {
        "manual": Transmission.MANUAL,
        "automatica": Transmission.AUTOMATIC,
        "automática": Transmission.AUTOMATIC,
        "automatic": Transmission.AUTOMATIC,
        "cvt": Transmission.CVT,
    }

    # Fuel type mapping
    FUEL_TYPE_MAP = {
        "gasolina": FuelType.GASOLINE,
        "diesel": FuelType.DIESEL,
        "híbrido": FuelType.HYBRID,
        "hibrido": FuelType.HYBRID,
        "hybrid": FuelType.HYBRID,
        "eléctrico": FuelType.ELECTRIC,
        "electrico": FuelType.ELECTRIC,
        "electric": FuelType.ELECTRIC,
    }

    def __init__(self):
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        })
        self._last_request_time = 0

    def _rate_limit(self):
        """Apply rate limiting between requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str) -> requests.Response:
        """Make a rate-limited GET request"""
        self._rate_limit()
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response

    def get_all_brands(self) -> list[dict]:
        """
        Get list of all brands available in the catalog

        Returns:
            List of dicts with brand name and URL
        """
        logger.info("Fetching all brands from Autocosmos catalog")
        brands = []

        try:
            response = self._get(self.CATALOG_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            # Find brand links - they're typically in a list or grid
            # URL pattern: /catalogo/vigente/{brand}
            brand_pattern = re.compile(r"/catalogo/vigente/([a-z0-9-]+)$", re.I)

            for link in soup.find_all("a", href=brand_pattern):
                href = link.get("href", "")
                match = brand_pattern.search(href)
                if match:
                    brand_slug = match.group(1)
                    brand_name = link.get_text(strip=True)
                    if not brand_name:
                        # Try to get from image alt or nearby text
                        img = link.find("img")
                        if img:
                            brand_name = img.get("alt", brand_slug)

                    brand_name = brand_name or brand_slug.replace("-", " ").title()

                    brands.append({
                        "name": brand_name,
                        "slug": brand_slug,
                        "url": urljoin(self.BASE_URL, href),
                    })

            # Remove duplicates
            seen = set()
            unique_brands = []
            for brand in brands:
                if brand["slug"] not in seen:
                    seen.add(brand["slug"])
                    unique_brands.append(brand)

            logger.info(f"Found {len(unique_brands)} brands")
            return sorted(unique_brands, key=lambda x: x["name"])

        except Exception as e:
            logger.error(f"Error fetching brands: {e}")
            return []

    def get_brand_models(self, brand_slug: str) -> list[dict]:
        """
        Get all models for a specific brand

        Args:
            brand_slug: Brand URL slug (e.g., "nissan", "toyota")

        Returns:
            List of model info dicts
        """
        logger.info(f"Fetching models for brand: {brand_slug}")
        models = []

        brand_url = f"{self.BASE_URL}/catalogo/vigente/{brand_slug}"

        try:
            response = self._get(brand_url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Find model links
            # URL pattern: /catalogo/vigente/{brand}/{model}
            model_pattern = re.compile(
                rf"/catalogo/vigente/{brand_slug}/([a-z0-9-]+)$", re.I
            )

            for link in soup.find_all("a", href=model_pattern):
                href = link.get("href", "")
                match = model_pattern.search(href)
                if match:
                    model_slug = match.group(1)
                    model_name = link.get_text(strip=True)

                    # Try to extract price if visible
                    price = None
                    parent = link.find_parent(["div", "article", "li"])
                    if parent:
                        price_elem = parent.find(string=re.compile(r"\$[\d,]+"))
                        if price_elem:
                            price = self._parse_price(price_elem)

                    models.append({
                        "name": model_name or model_slug.replace("-", " ").title(),
                        "slug": model_slug,
                        "url": urljoin(self.BASE_URL, href),
                        "base_price": price,
                    })

            # Remove duplicates
            seen = set()
            unique_models = []
            for model in models:
                if model["slug"] not in seen:
                    seen.add(model["slug"])
                    unique_models.append(model)

            logger.info(f"Found {len(unique_models)} models for {brand_slug}")
            return unique_models

        except Exception as e:
            logger.error(f"Error fetching models for {brand_slug}: {e}")
            return []

    def get_model_details(self, brand_slug: str, model_slug: str) -> Optional[NewCarModel]:
        """
        Get detailed info for a specific model including all versions and prices

        Args:
            brand_slug: Brand URL slug
            model_slug: Model URL slug

        Returns:
            NewCarModel with all version details
        """
        model_url = f"{self.BASE_URL}/catalogo/vigente/{brand_slug}/{model_slug}"
        logger.info(f"Fetching details for {brand_slug} {model_slug}")

        try:
            response = self._get(model_url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract model info
            brand_name = brand_slug.replace("-", " ").title()
            model_name = model_slug.replace("-", " ").title()

            # Try to get proper names from page
            h1 = soup.find("h1")
            if h1:
                title_text = h1.get_text(strip=True)
                # Title usually: "Brand Model Year"
                parts = title_text.split()
                if len(parts) >= 2:
                    brand_name = parts[0]
                    # Model is everything between brand and year
                    year_match = re.search(r"20\d{2}", title_text)
                    if year_match:
                        model_name = title_text[len(brand_name):year_match.start()].strip()

            # Get current year
            year = date.today().year
            year_match = re.search(r"20\d{2}", response.text)
            if year_match:
                year = int(year_match.group())

            # Extract versions and prices
            versions = self._extract_versions(soup)

            # Get base price (lowest version price)
            base_price = None
            if versions:
                base_price = min(v.price_mxn for v in versions)

            # Extract specs
            body_type = self._extract_body_type(soup)
            engine = self._extract_engine(soup)
            transmission = self._extract_transmission(soup)
            fuel_type = self._extract_fuel_type(soup)
            origin = self._extract_origin(soup)

            return NewCarModel(
                brand=brand_name,
                model=model_name,
                year=year,
                body_type=body_type,
                base_price_mxn=base_price,
                versions=versions,
                engine=engine,
                transmission=transmission,
                fuel_type=fuel_type,
                origin_country=origin,
                scraped_date=date.today(),
            )

        except Exception as e:
            logger.error(f"Error fetching model details for {brand_slug}/{model_slug}: {e}")
            return None

    def _extract_versions(self, soup: BeautifulSoup) -> list[NewCarVersion]:
        """Extract all versions/trims with prices"""
        versions = []

        # Look for version tables or lists
        # Common patterns: tables with version name and price columns
        # or repeated div/article elements

        # Try table first
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    name_cell = cells[0].get_text(strip=True)
                    price_cell = None
                    for cell in cells[1:]:
                        text = cell.get_text(strip=True)
                        if "$" in text or re.search(r"\d{3},\d{3}", text):
                            price_cell = text
                            break

                    if name_cell and price_cell:
                        price = self._parse_price(price_cell)
                        if price:
                            # Extract specs from row if available
                            engine = None
                            hp = None
                            trans = None

                            for cell in cells:
                                text = cell.get_text(strip=True).lower()
                                if "hp" in text or "cv" in text:
                                    hp_match = re.search(r"(\d+)\s*(hp|cv)", text)
                                    if hp_match:
                                        hp = int(hp_match.group(1))
                                if "l" in text and re.search(r"\d\.\d", text):
                                    engine = text
                                if "manual" in text:
                                    trans = Transmission.MANUAL
                                elif "auto" in text or "cvt" in text:
                                    trans = Transmission.CVT if "cvt" in text else Transmission.AUTOMATIC

                            versions.append(NewCarVersion(
                                name=name_cell,
                                price_mxn=price,
                                engine=engine,
                                horsepower=hp,
                                transmission=trans,
                            ))

        # If no table, try divs/articles
        if not versions:
            # Look for price patterns in the page
            price_pattern = re.compile(r"([\w\s-]+)\s*\$\s*([\d,]+)")
            text = soup.get_text()
            for match in price_pattern.finditer(text):
                name = match.group(1).strip()
                price = self._parse_price(f"${match.group(2)}")
                if price and len(name) > 2 and len(name) < 50:
                    versions.append(NewCarVersion(
                        name=name,
                        price_mxn=price,
                    ))

        # Deduplicate by name
        seen_names = set()
        unique_versions = []
        for v in versions:
            if v.name not in seen_names:
                seen_names.add(v.name)
                unique_versions.append(v)

        return unique_versions

    def _extract_body_type(self, soup: BeautifulSoup) -> Optional[VehicleType]:
        """Extract body type from page"""
        text = soup.get_text().lower()

        for keyword, body_type in self.BODY_TYPE_MAP.items():
            if keyword in text:
                return body_type

        # Check URL/breadcrumbs
        breadcrumbs = soup.find_all("a", href=re.compile(r"/catalogo/(sedan|suv|pickup|hatchback)", re.I))
        for bc in breadcrumbs:
            href = bc.get("href", "").lower()
            for keyword, body_type in self.BODY_TYPE_MAP.items():
                if keyword in href:
                    return body_type

        return None

    def _extract_engine(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract engine info"""
        # Look for patterns like "1.6L", "2.0T", "V6"
        patterns = [
            r"\d\.\d\s*[LT]",
            r"V\d",
            r"\d{3,4}\s*cc",
        ]

        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group().strip()

        return None

    def _extract_transmission(self, soup: BeautifulSoup) -> Optional[Transmission]:
        """Extract transmission type"""
        text = soup.get_text().lower()

        for keyword, trans in self.TRANSMISSION_MAP.items():
            if keyword in text:
                return trans

        return None

    def _extract_fuel_type(self, soup: BeautifulSoup) -> Optional[FuelType]:
        """Extract fuel type"""
        text = soup.get_text().lower()

        for keyword, fuel in self.FUEL_TYPE_MAP.items():
            if keyword in text:
                return fuel

        return FuelType.GASOLINE  # Default assumption

    def _extract_origin(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract country of origin"""
        text = soup.get_text().lower()

        origins = {
            "hecho en méxico": "Mexico",
            "made in mexico": "Mexico",
            "fabricado en méxico": "Mexico",
            "importado": "Imported",
            "china": "China",
            "india": "India",
            "japón": "Japan",
            "japan": "Japan",
            "corea": "South Korea",
            "korea": "South Korea",
            "usa": "USA",
            "estados unidos": "USA",
        }

        for keyword, origin in origins.items():
            if keyword in text:
                return origin

        return None

    def _parse_price(self, price_text: str) -> Optional[Decimal]:
        """Parse price string to Decimal"""
        if not price_text:
            return None

        # Extract numbers from string like "$362,900" or "362900"
        cleaned = re.sub(r"[^\d]", "", price_text)
        if cleaned:
            try:
                return Decimal(cleaned)
            except Exception:
                pass

        return None

    def scrape_all_models(
        self,
        brands: Optional[list[str]] = None,
        save_progress: bool = True
    ) -> Generator[NewCarModel, None, None]:
        """
        Scrape all models from all brands (or specific brands)

        Args:
            brands: Optional list of brand slugs to scrape
            save_progress: Whether to save progress to file

        Yields:
            NewCarModel objects
        """
        all_brands = self.get_all_brands()

        if brands:
            all_brands = [b for b in all_brands if b["slug"] in brands]

        total_models = 0
        progress_file = self.config.raw_data_path / "autocosmos" / "scrape_progress.json"
        progress_file.parent.mkdir(parents=True, exist_ok=True)

        for brand in all_brands:
            logger.info(f"Processing brand: {brand['name']}")

            models = self.get_brand_models(brand["slug"])

            for model_info in models:
                model = self.get_model_details(brand["slug"], model_info["slug"])
                if model:
                    total_models += 1
                    yield model

                    if save_progress and total_models % 10 == 0:
                        self._save_progress(progress_file, {
                            "total_models": total_models,
                            "current_brand": brand["name"],
                            "timestamp": str(date.today()),
                        })

        logger.info(f"Completed scraping {total_models} models")

    def _save_progress(self, path: Path, data: dict):
        """Save scraping progress"""
        with open(path, "w") as f:
            json.dump(data, f)

    def save_catalog(self, output_path: Optional[Path] = None):
        """
        Scrape and save full catalog to JSON file

        Args:
            output_path: Path to save catalog
        """
        if output_path is None:
            output_path = (
                self.config.raw_data_path / "autocosmos" /
                f"catalog_{date.today().isoformat()}.json"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        catalog = []
        for model in self.scrape_all_models():
            model_dict = {
                "brand": model.brand,
                "model": model.model,
                "year": model.year,
                "body_type": model.body_type.value if model.body_type else None,
                "base_price_mxn": str(model.base_price_mxn) if model.base_price_mxn else None,
                "engine": model.engine,
                "transmission": model.transmission.value if model.transmission else None,
                "fuel_type": model.fuel_type.value if model.fuel_type else None,
                "origin_country": model.origin_country,
                "scraped_date": model.scraped_date.isoformat() if model.scraped_date else None,
                "versions": [
                    {
                        "name": v.name,
                        "price_mxn": str(v.price_mxn),
                        "engine": v.engine,
                        "horsepower": v.horsepower,
                        "transmission": v.transmission.value if v.transmission else None,
                    }
                    for v in model.versions
                ],
            }
            catalog.append(model_dict)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved catalog with {len(catalog)} models to {output_path}")
        return output_path


def main():
    """Test the scraper"""
    logging.basicConfig(level=logging.INFO)

    scraper = AutocosmosScraper()

    # Test getting brands
    print("Fetching brands...")
    brands = scraper.get_all_brands()
    print(f"Found {len(brands)} brands")
    for brand in brands[:10]:
        print(f"  - {brand['name']}: {brand['url']}")

    # Test getting models for Nissan
    print("\nFetching Nissan models...")
    models = scraper.get_brand_models("nissan")
    print(f"Found {len(models)} models")
    for model in models[:5]:
        print(f"  - {model['name']}: {model.get('base_price', 'N/A')}")

    # Test getting model details
    print("\nFetching Nissan Versa details...")
    versa = scraper.get_model_details("nissan", "versa")
    if versa:
        print(f"  Brand: {versa.brand}")
        print(f"  Model: {versa.model}")
        print(f"  Year: {versa.year}")
        print(f"  Base Price: ${versa.base_price_mxn:,.0f} MXN" if versa.base_price_mxn else "  Base Price: N/A")
        print(f"  Body Type: {versa.body_type}")
        print(f"  Versions: {len(versa.versions)}")
        for v in versa.versions[:3]:
            print(f"    - {v.name}: ${v.price_mxn:,.0f} MXN")


if __name__ == "__main__":
    main()
