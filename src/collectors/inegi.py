"""
INEGI Data Collector for automotive industry data

Sources:
- RAIAVL (Registro Administrativo de la Industria Automotriz de Vehículos Ligeros)
  - Production, domestic sales, exports by brand/model
  - URL: https://www.inegi.org.mx/datosprimarios/iavl/

- VMRC (Vehículos de Motor Registrados en Circulación)
  - Vehicle registrations by state
  - URL: https://www.inegi.org.mx/programas/vehiculosmotor/
"""
import csv
import io
import json
import logging
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Generator, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..config import get_config
from ..models import INEGIProductionData, INEGIRegistrationData

logger = logging.getLogger(__name__)


class INEGICollector:
    """Collector for INEGI automotive data"""

    # Known URLs for INEGI data
    RAIAVL_BASE = "https://www.inegi.org.mx/datosprimarios/iavl/"
    RAIAVL_TABULADOS = "https://www.inegi.org.mx/app/tabulados/default.html?nc=100100090_a"
    VMRC_BASE = "https://www.inegi.org.mx/programas/vehiculosmotor/"

    # API endpoint
    API_BASE = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"

    # Known indicator IDs for automotive data (may need updating)
    INDICATORS = {
        "produccion_vehiculos_ligeros": "6207067854",
        "ventas_vehiculos_ligeros": "6207067855",
        "exportacion_vehiculos_ligeros": "6207067856",
    }

    def __init__(self):
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KAVAK-Market-Research/1.0",
            "Accept": "text/html,application/json,text/csv",
        })

    def fetch_raiavl_data(
        self,
        year: int,
        month: Optional[int] = None
    ) -> list[INEGIProductionData]:
        """
        Fetch RAIAVL data (production, sales, exports by brand)

        Args:
            year: Year to fetch
            month: Optional specific month (1-12), or None for full year

        Returns:
            List of INEGIProductionData records
        """
        logger.info(f"Fetching RAIAVL data for {year}" + (f"-{month:02d}" if month else ""))

        results = []

        # Try to fetch from interactive tables (CSV export)
        csv_url = self._build_raiavl_csv_url(year, month)
        if csv_url:
            try:
                results = self._fetch_raiavl_csv(csv_url, year, month)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"CSV fetch failed: {e}, trying API")

        # Fall back to API if available
        if self.config.inegi_api_token:
            try:
                results = self._fetch_raiavl_api(year, month)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"API fetch failed: {e}")

        # Last resort: scrape from tabulados page
        results = self._scrape_raiavl_page(year, month)
        return results

    def _build_raiavl_csv_url(self, year: int, month: Optional[int]) -> Optional[str]:
        """Build URL for CSV download from INEGI tabulados"""
        # INEGI uses specific query parameters for data export
        # Format: https://www.inegi.org.mx/app/tabulados/interactivos/?px=RAIAVL_X_Y&bd=RAIAVL
        base = "https://www.inegi.org.mx/app/tabulados/interactivos/"
        # The px parameter varies by table type
        return f"{base}?px=RAIAVL_8_9&bd=RAIAVL"

    def _fetch_raiavl_csv(
        self,
        url: str,
        year: int,
        month: Optional[int]
    ) -> list[INEGIProductionData]:
        """Fetch and parse RAIAVL CSV data"""
        results = []

        try:
            # First get the page to find CSV download link
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for CSV export link or form
            csv_link = soup.find("a", href=re.compile(r"\.csv", re.I))
            if csv_link:
                csv_url = urljoin(url, csv_link["href"])
                csv_response = self.session.get(csv_url, timeout=30)
                csv_response.raise_for_status()

                # Parse CSV
                reader = csv.DictReader(io.StringIO(csv_response.text))
                for row in reader:
                    data = self._parse_raiavl_row(row, year, month)
                    if data:
                        results.append(data)

        except Exception as e:
            logger.error(f"Error fetching RAIAVL CSV: {e}")
            raise

        return results

    def _fetch_raiavl_api(
        self,
        year: int,
        month: Optional[int]
    ) -> list[INEGIProductionData]:
        """Fetch RAIAVL data via INEGI API"""
        results = []
        token = self.config.inegi_api_token

        if not token or token.startswith("${"):
            logger.warning("INEGI API token not configured")
            return results

        for indicator_name, indicator_id in self.INDICATORS.items():
            try:
                # Build API URL
                # Format: /INDICATOR/{id}/{lang}/{area}/{recent}/{source}/{version}/{token}
                api_url = (
                    f"{self.API_BASE}/INDICATOR/{indicator_id}/es/00/false/BISE/2.0/{token}"
                    "?type=json"
                )

                response = self.session.get(api_url, timeout=30)
                response.raise_for_status()

                data = response.json()
                series = data.get("Series", [])

                for serie in series:
                    observations = serie.get("OBSERVATIONS", [])
                    for obs in observations:
                        period = obs.get("TIME_PERIOD", "")
                        value = obs.get("OBS_VALUE", 0)

                        # Filter by year/month
                        if period.startswith(str(year)):
                            if month is None or period.endswith(f"-{month:02d}"):
                                results.append(INEGIProductionData(
                                    period=period,
                                    brand="Total",
                                    **{indicator_name.replace("_vehiculos_ligeros", "_units"): int(value)}
                                ))

            except Exception as e:
                logger.error(f"Error fetching indicator {indicator_name}: {e}")

        return results

    def _scrape_raiavl_page(
        self,
        year: int,
        month: Optional[int]
    ) -> list[INEGIProductionData]:
        """Scrape RAIAVL data from INEGI website tables"""
        results = []

        try:
            response = self.session.get(self.RAIAVL_TABULADOS, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find data tables
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                headers = []
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    if not headers:
                        headers = [c.get_text(strip=True) for c in cells]
                        continue

                    values = [c.get_text(strip=True) for c in cells]
                    if len(values) >= 2:
                        # Parse row based on table structure
                        data = self._parse_table_row(headers, values, year, month)
                        if data:
                            results.append(data)

        except Exception as e:
            logger.error(f"Error scraping RAIAVL page: {e}")

        return results

    def _parse_raiavl_row(
        self,
        row: dict,
        year: int,
        month: Optional[int]
    ) -> Optional[INEGIProductionData]:
        """Parse a CSV row into INEGIProductionData"""
        try:
            # CSV columns may vary, adapt based on actual format
            brand = row.get("Marca", row.get("marca", row.get("Brand", "")))
            model = row.get("Modelo", row.get("modelo", row.get("Model", "")))

            production = self._parse_int(row.get("Produccion", row.get("produccion", 0)))
            sales = self._parse_int(row.get("Ventas", row.get("ventas", 0)))
            exports = self._parse_int(row.get("Exportacion", row.get("exportacion", 0)))

            period_str = row.get("Periodo", row.get("periodo", f"{year}"))
            if month:
                period_str = f"{year}-{month:02d}"

            return INEGIProductionData(
                period=period_str,
                brand=brand,
                model=model if model else None,
                production_units=production,
                domestic_sales_units=sales,
                export_units=exports,
            )
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            return None

    def _parse_table_row(
        self,
        headers: list,
        values: list,
        year: int,
        month: Optional[int]
    ) -> Optional[INEGIProductionData]:
        """Parse an HTML table row"""
        try:
            row_dict = dict(zip(headers, values))
            return self._parse_raiavl_row(row_dict, year, month)
        except Exception:
            return None

    def _parse_int(self, value) -> int:
        """Safely parse integer from various formats"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            # Remove commas, spaces, and other formatting
            cleaned = re.sub(r"[,\s]", "", value)
            try:
                return int(cleaned)
            except ValueError:
                return 0
        return 0

    def fetch_vmrc_data(
        self,
        year: int,
        month: Optional[int] = None,
        state: Optional[str] = None
    ) -> list[INEGIRegistrationData]:
        """
        Fetch VMRC data (vehicle registrations by state)

        Args:
            year: Year to fetch
            month: Optional specific month
            state: Optional state filter

        Returns:
            List of INEGIRegistrationData records
        """
        logger.info(f"Fetching VMRC data for {year}" + (f"-{month:02d}" if month else ""))

        results = []

        # VMRC data URL
        vmrc_url = f"{self.VMRC_BASE}default.html"

        try:
            response = self.session.get(vmrc_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for data links or embedded data
            # This will need adaptation based on actual page structure
            data_links = soup.find_all("a", href=re.compile(r"\.csv|\.xlsx", re.I))

            for link in data_links:
                file_url = urljoin(vmrc_url, link["href"])
                if ".csv" in file_url.lower():
                    results.extend(self._fetch_vmrc_csv(file_url, year, month, state))

        except Exception as e:
            logger.error(f"Error fetching VMRC data: {e}")

        return results

    def _fetch_vmrc_csv(
        self,
        url: str,
        year: int,
        month: Optional[int],
        state: Optional[str]
    ) -> list[INEGIRegistrationData]:
        """Fetch and parse VMRC CSV data"""
        results = []

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            reader = csv.DictReader(io.StringIO(response.text))
            for row in reader:
                # Filter by year/month/state as needed
                row_year = row.get("Anio", row.get("Year", ""))
                if str(year) not in str(row_year):
                    continue

                row_state = row.get("Entidad", row.get("State", ""))
                if state and state.lower() not in row_state.lower():
                    continue

                results.append(INEGIRegistrationData(
                    period=f"{year}-{month:02d}" if month else str(year),
                    state=row_state,
                    state_code=row.get("Clave", row.get("Code", "")),
                    vehicle_class=row.get("Clase", row.get("Class", "automovil")),
                    service_type=row.get("Tipo_Servicio", row.get("Service", "particular")),
                    total_registered=self._parse_int(row.get("Total", 0)),
                ))

        except Exception as e:
            logger.error(f"Error fetching VMRC CSV: {e}")

        return results

    def download_monthly_bulletin(
        self,
        year: int,
        month: int,
        save_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Download the monthly RAIAVL bulletin PDF

        Args:
            year: Year
            month: Month (1-12)
            save_path: Optional path to save file

        Returns:
            Path to downloaded file, or None if failed
        """
        # Bulletin URL pattern
        # Example: https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/rm_raiavl/rm_raiavl2025_01.pdf
        bulletin_url = (
            f"https://www.inegi.org.mx/contenidos/saladeprensa/boletines/"
            f"{year}/rm_raiavl/rm_raiavl{year}_{month:02d}.pdf"
        )

        if save_path is None:
            save_path = self.config.raw_data_path / "inegi" / f"raiavl_{year}_{month:02d}.pdf"

        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = self.session.get(bulletin_url, timeout=60)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded bulletin to {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"Error downloading bulletin: {e}")
            return None

    def get_available_periods(self) -> list[str]:
        """Get list of available data periods from INEGI"""
        periods = []

        try:
            response = self.session.get(self.RAIAVL_BASE, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for period selectors or date references
            # Extract years and months mentioned
            year_pattern = re.compile(r"20\d{2}")
            years = set(year_pattern.findall(response.text))

            for year in sorted(years, reverse=True):
                for month in range(1, 13):
                    periods.append(f"{year}-{month:02d}")

        except Exception as e:
            logger.error(f"Error getting available periods: {e}")

        return periods[:24]  # Return last 24 months


def main():
    """Test the collector"""
    logging.basicConfig(level=logging.INFO)

    collector = INEGICollector()

    # Test fetching current year data
    print("Fetching RAIAVL data for 2025...")
    data = collector.fetch_raiavl_data(2025)
    print(f"Found {len(data)} records")

    for record in data[:5]:
        print(f"  {record.brand}: {record.production_units} produced, "
              f"{record.domestic_sales_units} sold")

    # Test downloading bulletin
    print("\nDownloading latest bulletin...")
    path = collector.download_monthly_bulletin(2025, 10)
    if path:
        print(f"Downloaded to: {path}")


if __name__ == "__main__":
    main()
