#!/usr/bin/env python3
"""
Monthly Market Research Runner

Executes the full monthly market research workflow:
1. Collect new car data from Autocosmos
2. Fetch INEGI production/sales data
3. Generate analysis reports
4. Output Excel, CSV, and text reports

Usage:
    python run_monthly.py --month 2025-01
    python run_monthly.py --month 2025-01 --brands nissan,toyota,honda
    python run_monthly.py --month 2025-01 --skip-collection
"""
import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.collectors import AutocosmosScraper, INEGICollector
from src.analyzers import NewCarAnalyzer
from src.reporters import ExcelReporter, generate_csv_exports
from src.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_month(month_str: str) -> tuple[int, int]:
    """Parse YYYY-MM format to (year, month)"""
    parts = month_str.split("-")
    return int(parts[0]), int(parts[1])


def collect_autocosmos(brands: list = None):
    """Collect new car data from Autocosmos"""
    logger.info("=" * 50)
    logger.info("STEP 1: Collecting Autocosmos new car data")
    logger.info("=" * 50)

    scraper = AutocosmosScraper()
    config = get_config()

    # Get all brands
    all_brands = scraper.get_all_brands()
    logger.info(f"Found {len(all_brands)} brands in catalog")

    # Filter if specified
    if brands:
        all_brands = [b for b in all_brands if b["slug"] in brands]
        logger.info(f"Filtering to {len(all_brands)} specified brands")

    # Collect models
    catalog = []
    for brand in all_brands:
        logger.info(f"Processing {brand['name']}...")
        models = scraper.get_brand_models(brand["slug"])

        for model_info in models:
            model = scraper.get_model_details(brand["slug"], model_info["slug"])
            if model:
                catalog.append(model)

    # Save catalog
    import json
    output_dir = config.raw_data_path / "autocosmos"
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_file = output_dir / f"catalog_{date.today().isoformat()}.json"

    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "brand": m.brand,
                    "model": m.model,
                    "year": m.year,
                    "body_type": m.body_type.value if m.body_type else None,
                    "base_price_mxn": str(m.base_price_mxn) if m.base_price_mxn else None,
                    "transmission": m.transmission.value if m.transmission else None,
                    "fuel_type": m.fuel_type.value if m.fuel_type else None,
                    "origin_country": m.origin_country,
                    "scraped_date": m.scraped_date.isoformat() if m.scraped_date else None,
                    "versions": [
                        {
                            "name": v.name,
                            "price_mxn": str(v.price_mxn),
                        }
                        for v in m.versions
                    ],
                }
                for m in catalog
            ],
            f,
            ensure_ascii=False,
            indent=2
        )

    logger.info(f"Saved {len(catalog)} models to {catalog_file}")
    return catalog_file


def collect_inegi(year: int, month: int):
    """Collect INEGI data"""
    logger.info("=" * 50)
    logger.info("STEP 2: Collecting INEGI data")
    logger.info("=" * 50)

    collector = INEGICollector()
    config = get_config()

    # Fetch RAIAVL data
    raiavl_data = collector.fetch_raiavl_data(year, month)
    logger.info(f"Fetched {len(raiavl_data)} RAIAVL records")

    # Download bulletin
    bulletin = collector.download_monthly_bulletin(year, month)
    if bulletin:
        logger.info(f"Downloaded bulletin: {bulletin}")

    return len(raiavl_data)


def generate_reports(catalog_path: Path = None):
    """Generate all reports"""
    logger.info("=" * 50)
    logger.info("STEP 3: Generating reports")
    logger.info("=" * 50)

    # Text report
    analyzer = NewCarAnalyzer(catalog_path)
    report = analyzer.generate_report()

    config = get_config()
    text_file = config.output_path / f"new_car_report_{date.today().isoformat()}.txt"
    text_file.parent.mkdir(parents=True, exist_ok=True)

    with open(text_file, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Generated text report: {text_file}")

    # Excel report
    reporter = ExcelReporter()
    excel_file = reporter.generate_new_car_report(catalog_path=catalog_path)
    logger.info(f"Generated Excel report: {excel_file}")

    # CSV exports
    csv_files = generate_csv_exports(catalog_path)
    logger.info(f"Generated {len(csv_files)} CSV files")

    return {
        "text": text_file,
        "excel": excel_file,
        "csv": csv_files,
    }


def print_summary(reports: dict):
    """Print summary of generated reports"""
    logger.info("=" * 50)
    logger.info("MONTHLY MARKET RESEARCH COMPLETE")
    logger.info("=" * 50)
    logger.info("")
    logger.info("Generated reports:")
    logger.info(f"  - Text:  {reports['text']}")
    logger.info(f"  - Excel: {reports['excel']}")
    logger.info("  - CSV files:")
    for f in reports['csv']:
        logger.info(f"      {f}")
    logger.info("")


def main():
    parser = argparse.ArgumentParser(description="Run monthly market research")
    parser.add_argument(
        "--month",
        type=str,
        default=date.today().strftime("%Y-%m"),
        help="Month to analyze (YYYY-MM format)"
    )
    parser.add_argument(
        "--brands",
        type=str,
        help="Comma-separated brand slugs to collect (default: all)"
    )
    parser.add_argument(
        "--skip-collection",
        action="store_true",
        help="Skip data collection, use existing data"
    )
    parser.add_argument(
        "--skip-inegi",
        action="store_true",
        help="Skip INEGI collection"
    )

    args = parser.parse_args()
    year, month = parse_month(args.month)
    brands = args.brands.split(",") if args.brands else None

    logger.info(f"Running monthly market research for {args.month}")
    logger.info("")

    catalog_path = None

    # Step 1: Collect Autocosmos data
    if not args.skip_collection:
        catalog_path = collect_autocosmos(brands)
    else:
        logger.info("Skipping data collection (--skip-collection)")

    # Step 2: Collect INEGI data
    if not args.skip_collection and not args.skip_inegi:
        collect_inegi(year, month)
    else:
        logger.info("Skipping INEGI collection")

    # Step 3: Generate reports
    reports = generate_reports(catalog_path)

    # Print summary
    print_summary(reports)


if __name__ == "__main__":
    main()
