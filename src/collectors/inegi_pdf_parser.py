"""
INEGI RAIAVL Bulletin PDF Parser
Extracts vehicle sales, production, and export data from monthly PDF bulletins.
"""
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RAIAVLMonthlyData:
    """Parsed data from RAIAVL monthly bulletin"""
    period: str  # e.g., "2025-10"
    year: int
    month: int

    # Monthly totals
    monthly_sales: int
    monthly_production: int
    monthly_exports: int

    # Year-to-date totals
    ytd_sales: int
    ytd_production: int
    ytd_exports: int

    # Year-over-year variations
    sales_yoy_pct: float
    production_yoy_pct: float
    exports_yoy_pct: float

    # Brand breakdown (list of dicts)
    brand_sales: list


@dataclass
class BrandSalesData:
    """Brand-level sales data"""
    brand: str
    monthly_current: int
    monthly_previous: int
    monthly_variation_pct: float
    ytd_current: int
    ytd_previous: int
    ytd_variation_pct: float


def parse_raiavl_bulletin(pdf_path: Path) -> Optional[RAIAVLMonthlyData]:
    """
    Parse an INEGI RAIAVL bulletin PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        RAIAVLMonthlyData object with extracted data
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install PyMuPDF")
        return None

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()

        return _parse_bulletin_text(full_text, pdf_path)

    except Exception as e:
        logger.error(f"Error parsing PDF {pdf_path}: {e}")
        return None


def _parse_bulletin_text(text: str, pdf_path: Path) -> Optional[RAIAVLMonthlyData]:
    """Parse the extracted text from the bulletin"""

    # Extract period from text (the bulletin reports data for the PREVIOUS month)
    # e.g., November bulletin (raiavl_2025_11) reports October data
    month_names = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    # Find the data month from the text
    # Look for the month mentioned in the summary section (second occurrence is usually data month)
    all_months = re.findall(
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(\d{4})",
        text.lower()
    )
    # The data month is usually the second unique month mentioned (first is publication date)
    data_month_match = None
    if len(all_months) >= 2:
        data_month_match = all_months[1]  # Second occurrence
    elif all_months:
        data_month_match = all_months[0]
    if data_month_match:
        month = month_names.get(data_month_match[0], 1)
        year = int(data_month_match[1])
    else:
        # Fall back to filename
        filename = pdf_path.stem
        match = re.search(r"(\d{4})_(\d{2})", filename)
        if match:
            year = int(match.group(1))
            # Bulletin month - 1 = data month
            bulletin_month = int(match.group(2))
            month = bulletin_month - 1 if bulletin_month > 1 else 12
            if bulletin_month == 1:
                year -= 1
        else:
            logger.error("Could not determine period from PDF")
            return None

    period = f"{year}-{month:02d}"

    month_names_es = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    current_month_name = month_names_es[month - 1]

    monthly_sales = 0
    monthly_production = 0
    monthly_exports = 0
    ytd_sales = 0
    ytd_production = 0
    ytd_exports = 0

    # Parse by scanning for month name and collecting numbers from following lines
    lines = text.split('\n')
    found_monthly = False
    found_ytd = False

    for i, line in enumerate(lines):
        line_clean = line.strip()

        # Look for monthly data row (just the month name, e.g., "Octubre")
        # Only use the first occurrence with valid numbers
        if not found_monthly and line_clean == current_month_name and i < len(lines) - 10:
            numbers = []
            for j in range(i+1, min(i+15, len(lines))):
                nums = re.findall(r'[\d][\d\s]*[\d]', lines[j])
                for n in nums:
                    val = int(n.replace(' ', ''))
                    if val > 1000:  # Filter small numbers
                        numbers.append(val)
                # Stop when we hit the next section
                if 'Enero-' in lines[j]:
                    break

            if len(numbers) >= 6:
                # Format: prev_sales, prev_prod, prev_exp, curr_sales, curr_prod, curr_exp
                monthly_sales = numbers[3]
                monthly_production = numbers[4]
                monthly_exports = numbers[5]
                found_monthly = True
                logger.debug(f"Monthly data: {monthly_sales}, {monthly_production}, {monthly_exports}")

        # Look for YTD row (Enero-MONTH) - immediately after monthly data
        ytd_pattern = f"enero-{current_month_name.lower()}"  # all lowercase for comparison
        if not found_ytd and ytd_pattern in line_clean.lower() and i < len(lines) - 10:
            numbers = []
            for j in range(i+1, min(i+15, len(lines))):
                nums = re.findall(r'[\d][\d\s]*[\d]', lines[j])
                for n in nums:
                    val = int(n.replace(' ', ''))
                    if val > 10000:  # YTD numbers are bigger
                        numbers.append(val)
                # Stop at footnote or next section
                if '1/' in lines[j] or 'Fuente' in lines[j]:
                    break

            if len(numbers) >= 6:
                ytd_sales = numbers[3]
                ytd_production = numbers[4]
                ytd_exports = numbers[5]
                found_ytd = True
                logger.debug(f"YTD data: {ytd_sales}, {ytd_production}, {ytd_exports}")

        # Once we have both, stop searching
        if found_monthly and found_ytd:
            break

    # Extract YoY variations from summary section
    sales_yoy = _extract_variation(text, 'ventas', 'variación')
    production_yoy = _extract_variation(text, 'producción', 'variación')
    exports_yoy = _extract_variation(text, 'exportación', 'variación')

    # Parse brand breakdown table
    brand_sales = _parse_brand_table(text, year, month)

    return RAIAVLMonthlyData(
        period=period,
        year=year,
        month=month,
        monthly_sales=monthly_sales,
        monthly_production=monthly_production,
        monthly_exports=monthly_exports,
        ytd_sales=ytd_sales,
        ytd_production=ytd_production,
        ytd_exports=ytd_exports,
        sales_yoy_pct=sales_yoy,
        production_yoy_pct=production_yoy,
        exports_yoy_pct=exports_yoy,
        brand_sales=brand_sales,
    )


def _parse_number(s: str) -> int:
    """Parse a number string, removing spaces and commas"""
    cleaned = re.sub(r'[\s,]', '', s)
    try:
        return int(cleaned)
    except ValueError:
        return 0


def _extract_variation(text: str, keyword: str, prefix: str) -> float:
    """Extract percentage variation from text"""
    pattern = rf"{keyword}.*?([+-]?\d+\.?\d*)\s*%"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return 0.0


def _parse_brand_table(text: str, year: int, month: int) -> list:
    """Parse the brand-by-brand sales table"""
    brands = []

    # Known brand patterns
    brand_patterns = [
        'Acura', 'Audi', 'Bentley', 'BMW', 'Chirey', 'Ford', 'General Motors',
        'Honda', 'Hyundai', 'Infiniti', 'Isuzu', 'Jaguar', 'KIA', 'Land Rover',
        'Lexus', 'Lincoln', 'Mazda', 'Mercedes', 'MG Motor', 'Mitsubishi',
        'Nissan', 'Peugeot', 'Porsche', 'Renault', 'SEAT', 'Stellantis',
        'Subaru', 'Suzuki', 'Toyota', 'Volkswagen', 'Volvo'
    ]

    lines = text.split('\n')
    for line in lines:
        line_clean = line.strip()

        for brand in brand_patterns:
            if line_clean.startswith(brand):
                # Extract numbers from this line
                numbers = re.findall(r'-?\d[\d\s,]*\.?\d*', line_clean[len(brand):])
                numbers = [_parse_number_or_float(n) for n in numbers]
                numbers = [n for n in numbers if n is not None]

                if len(numbers) >= 4:
                    brands.append(BrandSalesData(
                        brand=brand,
                        monthly_previous=int(numbers[0]) if numbers[0] else 0,
                        monthly_current=int(numbers[1]) if len(numbers) > 1 and numbers[1] else 0,
                        monthly_variation_pct=float(numbers[2]) if len(numbers) > 2 else 0.0,
                        ytd_previous=int(numbers[3]) if len(numbers) > 3 and numbers[3] else 0,
                        ytd_current=int(numbers[4]) if len(numbers) > 4 and numbers[4] else 0,
                        ytd_variation_pct=float(numbers[5]) if len(numbers) > 5 else 0.0,
                    ))
                break

    return brands


def _parse_number_or_float(s: str):
    """Parse a number that might be int or float"""
    cleaned = re.sub(r'[\s,]', '', s)
    try:
        if '.' in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return None


def main():
    """Test the parser"""
    import logging
    logging.basicConfig(level=logging.INFO)

    # Test with a downloaded bulletin
    pdf_path = Path("data/raw/inegi/raiavl_2025_11.pdf")
    if pdf_path.exists():
        data = parse_raiavl_bulletin(pdf_path)
        if data:
            print(f"Period: {data.period}")
            print(f"Monthly: {data.monthly_sales:,} sales, {data.monthly_production:,} production, {data.monthly_exports:,} exports")
            print(f"YTD: {data.ytd_sales:,} sales, {data.ytd_production:,} production, {data.ytd_exports:,} exports")
            print(f"\nBrands found: {len(data.brand_sales)}")
            for brand in data.brand_sales[:10]:
                print(f"  {brand.brand}: {brand.monthly_current:,} (YTD: {brand.ytd_current:,})")
    else:
        print(f"PDF not found: {pdf_path}")


if __name__ == "__main__":
    main()
