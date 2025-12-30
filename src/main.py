"""
Main entry point for KAVAK Market Research

Usage:
    python -m src.main collect --source inegi --year 2025
    python -m src.main collect --source autocosmos --brands nissan,toyota
    python -m src.main report --month 2025-01
"""
import argparse
import json
import logging
from datetime import date
from pathlib import Path

from .collectors import AutocosmosScraper, INEGICollector
from .config import get_config
from .processors import get_standardizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def collect_inegi(year: int, month: int = None, output_dir: Path = None):
    """Collect INEGI data"""
    logger.info(f"Collecting INEGI data for {year}" + (f"-{month:02d}" if month else ""))

    config = get_config()
    collector = INEGICollector()

    if output_dir is None:
        output_dir = config.raw_data_path / "inegi"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch RAIAVL data (production, sales, exports)
    raiavl_data = collector.fetch_raiavl_data(year, month)
    logger.info(f"Fetched {len(raiavl_data)} RAIAVL records")

    # Save to JSON
    filename = f"raiavl_{year}" + (f"_{month:02d}" if month else "") + ".json"
    output_file = output_dir / filename
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "period": r.period,
                    "brand": r.brand,
                    "model": r.model,
                    "production_units": r.production_units,
                    "domestic_sales_units": r.domestic_sales_units,
                    "export_units": r.export_units,
                    "source": r.source,
                }
                for r in raiavl_data
            ],
            f,
            ensure_ascii=False,
            indent=2
        )
    logger.info(f"Saved RAIAVL data to {output_file}")

    # Download monthly bulletin if specific month
    if month:
        bulletin_path = collector.download_monthly_bulletin(year, month)
        if bulletin_path:
            logger.info(f"Downloaded bulletin to {bulletin_path}")

    # Fetch VMRC data (registrations by state)
    vmrc_data = collector.fetch_vmrc_data(year, month)
    if vmrc_data:
        logger.info(f"Fetched {len(vmrc_data)} VMRC records")
        vmrc_filename = f"vmrc_{year}" + (f"_{month:02d}" if month else "") + ".json"
        vmrc_file = output_dir / vmrc_filename
        with open(vmrc_file, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "period": r.period,
                        "state": r.state,
                        "state_code": r.state_code,
                        "vehicle_class": r.vehicle_class,
                        "service_type": r.service_type,
                        "total_registered": r.total_registered,
                        "source": r.source,
                    }
                    for r in vmrc_data
                ],
                f,
                ensure_ascii=False,
                indent=2
            )
        logger.info(f"Saved VMRC data to {vmrc_file}")

    return len(raiavl_data) + len(vmrc_data)


def collect_autocosmos(brands: list = None, output_dir: Path = None):
    """Collect Autocosmos new car prices"""
    logger.info("Collecting Autocosmos new car prices")

    config = get_config()
    scraper = AutocosmosScraper()

    if output_dir is None:
        output_dir = config.raw_data_path / "autocosmos"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all brands first
    all_brands = scraper.get_all_brands()
    logger.info(f"Found {len(all_brands)} brands in catalog")

    # Save brand list
    brands_file = output_dir / "brands.json"
    with open(brands_file, "w", encoding="utf-8") as f:
        json.dump(all_brands, f, ensure_ascii=False, indent=2)

    # Filter brands if specified
    if brands:
        all_brands = [b for b in all_brands if b["slug"] in brands]
        logger.info(f"Filtering to {len(all_brands)} specified brands")

    # Collect model data
    catalog = []
    standardizer = get_standardizer()

    for brand in all_brands:
        logger.info(f"Processing {brand['name']}...")

        models = scraper.get_brand_models(brand["slug"])
        logger.info(f"  Found {len(models)} models")

        for model_info in models:
            model = scraper.get_model_details(brand["slug"], model_info["slug"])
            if model:
                # Standardize
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

                # Add standardized fields
                model_dict = standardizer.standardize_record(model_dict)
                catalog.append(model_dict)

    # Save catalog
    catalog_file = output_dir / f"catalog_{date.today().isoformat()}.json"
    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(catalog)} models to {catalog_file}")
    return len(catalog)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="KAVAK Market Research")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect data from sources")
    collect_parser.add_argument(
        "--source",
        choices=["inegi", "autocosmos", "all"],
        default="all",
        help="Data source to collect from"
    )
    collect_parser.add_argument(
        "--year",
        type=int,
        default=date.today().year,
        help="Year to collect (for INEGI)"
    )
    collect_parser.add_argument(
        "--month",
        type=int,
        help="Month to collect (for INEGI)"
    )
    collect_parser.add_argument(
        "--brands",
        type=str,
        help="Comma-separated brand slugs (for Autocosmos)"
    )

    # Report command (placeholder)
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument(
        "--month",
        type=str,
        required=True,
        help="Month to report on (YYYY-MM format)"
    )

    args = parser.parse_args()

    if args.command == "collect":
        if args.source in ["inegi", "all"]:
            collect_inegi(args.year, args.month)

        if args.source in ["autocosmos", "all"]:
            brands = args.brands.split(",") if args.brands else None
            collect_autocosmos(brands)

    elif args.command == "report":
        logger.info(f"Report generation for {args.month} not yet implemented")
        # TODO: Implement report generation

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
