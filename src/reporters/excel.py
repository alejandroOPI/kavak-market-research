"""
Excel Report Generator for Market Research

Generates Excel workbooks with:
- Summary sheet
- Brand analysis
- Segment analysis
- Full catalog data
"""
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from ..analyzers.new_cars import NewCarAnalyzer
from ..config import get_config

logger = logging.getLogger(__name__)


class ExcelReporter:
    """Generate Excel reports from market data"""

    def __init__(self):
        self.config = get_config()

    def generate_new_car_report(
        self,
        output_path: Optional[Path] = None,
        catalog_path: Optional[Path] = None
    ) -> Path:
        """
        Generate Excel report for new car data

        Args:
            output_path: Path for output file
            catalog_path: Path to catalog JSON

        Returns:
            Path to generated file
        """
        if output_path is None:
            output_path = (
                self.config.output_path /
                f"kavak_new_cars_{date.today().isoformat()}.xlsx"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load analyzer
        analyzer = NewCarAnalyzer(catalog_path)

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            workbook = writer.book

            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#1a1a2e',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
            })

            money_format = workbook.add_format({
                'num_format': '$#,##0',
                'align': 'right',
            })

            pct_format = workbook.add_format({
                'num_format': '0.0%',
                'align': 'right',
            })

            # 1. Summary Sheet
            self._write_summary_sheet(writer, analyzer, header_format)

            # 2. Brand Analysis Sheet
            self._write_brand_sheet(writer, analyzer, header_format, money_format)

            # 3. Segment Analysis Sheet
            self._write_segment_sheet(writer, analyzer, header_format, money_format)

            # 4. Full Catalog Sheet
            self._write_catalog_sheet(writer, analyzer, header_format, money_format)

            # 5. EV/Hybrid Sheet
            self._write_ev_sheet(writer, analyzer, header_format, money_format, pct_format)

        logger.info(f"Generated Excel report: {output_path}")
        return output_path

    def _write_summary_sheet(self, writer, analyzer, header_format):
        """Write summary sheet"""
        summary = analyzer.get_summary()

        data = {
            'Metric': [
                'Report Date',
                'Catalog Date',
                'Total Models',
                'Total Brands',
                'Minimum Price',
                'Maximum Price',
                'Average Price',
                'Median Price',
            ],
            'Value': [
                date.today().isoformat(),
                summary['catalog_date'],
                summary['total_models'],
                summary['total_brands'],
                summary['price_min'],
                summary['price_max'],
                summary['price_avg'],
                summary['price_median'],
            ]
        }

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Summary', index=False, startrow=1)

        # Format header
        worksheet = writer.sheets['Summary']
        worksheet.write(0, 0, 'KAVAK Market Research - New Car Summary', header_format)
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 25)

    def _write_brand_sheet(self, writer, analyzer, header_format, money_format):
        """Write brand analysis sheet"""
        brand_stats = analyzer.get_brand_stats()

        data = []
        for stat in brand_stats:
            data.append({
                'Brand': stat.brand,
                'Model Count': stat.model_count,
                'Min Price (MXN)': float(stat.min_price),
                'Max Price (MXN)': float(stat.max_price),
                'Avg Price (MXN)': float(stat.avg_price),
                'Median Price (MXN)': float(stat.median_price),
                'Has EV': 'Yes' if stat.has_ev else 'No',
                'Has Hybrid': 'Yes' if stat.has_hybrid else 'No',
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='By Brand', index=False, startrow=1)

        # Format
        worksheet = writer.sheets['By Brand']
        worksheet.write(0, 0, 'Analysis by Brand', header_format)

        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:F', 18)
        worksheet.set_column('G:H', 12)

        # Apply money format to price columns
        for row in range(2, len(data) + 2):
            for col in range(2, 6):
                worksheet.write(row, col, data[row-2][list(data[0].keys())[col]], money_format)

    def _write_segment_sheet(self, writer, analyzer, header_format, money_format):
        """Write segment analysis sheet"""
        segment_stats = analyzer.get_segment_stats()

        data = []
        for stat in segment_stats:
            data.append({
                'Segment': stat.segment_label,
                'Model Count': stat.model_count,
                'Brand Count': stat.brand_count,
                'Min Price (MXN)': float(stat.min_price),
                'Max Price (MXN)': float(stat.max_price),
                'Avg Price (MXN)': float(stat.avg_price),
                'Brands': ', '.join(stat.brands[:5]),
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='By Segment', index=False, startrow=1)

        # Format
        worksheet = writer.sheets['By Segment']
        worksheet.write(0, 0, 'Analysis by Price Segment', header_format)
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:C', 12)
        worksheet.set_column('D:F', 18)
        worksheet.set_column('G:G', 40)

    def _write_catalog_sheet(self, writer, analyzer, header_format, money_format):
        """Write full catalog sheet"""
        data = []
        for car in analyzer.catalog:
            data.append({
                'Brand': car.get('brand', ''),
                'Model': car.get('model', ''),
                'Year': car.get('year', ''),
                'Body Type': car.get('body_type', ''),
                'Base Price (MXN)': float(car['base_price_mxn']) if car.get('base_price_mxn') else None,
                'Price Bucket': car.get('price_bucket', ''),
                'Transmission': car.get('transmission', ''),
                'Fuel Type': car.get('fuel_type', ''),
                'Origin': car.get('origin_country', ''),
                'Is EV': 'Yes' if car.get('is_ev') else 'No',
                'Is Hybrid': 'Yes' if car.get('is_hybrid') else 'No',
                'Versions Count': len(car.get('versions', [])),
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Full Catalog', index=False, startrow=1)

        # Format
        worksheet = writer.sheets['Full Catalog']
        worksheet.write(0, 0, 'Full New Car Catalog', header_format)

        # Set column widths
        col_widths = [15, 20, 8, 12, 18, 12, 12, 12, 12, 8, 10, 14]
        for i, width in enumerate(col_widths):
            worksheet.set_column(i, i, width)

        # Add autofilter
        worksheet.autofilter(1, 0, len(data) + 1, len(col_widths) - 1)

    def _write_ev_sheet(self, writer, analyzer, header_format, money_format, pct_format):
        """Write EV/Hybrid analysis sheet"""
        ev_stats = analyzer.get_ev_hybrid_stats()

        # Summary data
        summary_data = {
            'Category': ['Electric Vehicles', 'Hybrid Vehicles', 'Traditional', 'Total'],
            'Count': [
                ev_stats['ev_count'],
                ev_stats['hybrid_count'],
                ev_stats['total_models'] - ev_stats['ev_count'] - ev_stats['hybrid_count'],
                ev_stats['total_models']
            ],
            'Percentage': [
                ev_stats['ev_pct'] / 100,
                ev_stats['hybrid_pct'] / 100,
                (100 - ev_stats['ev_pct'] - ev_stats['hybrid_pct']) / 100,
                1.0
            ],
            'Avg Price (MXN)': [
                ev_stats['ev_avg_price'],
                ev_stats['hybrid_avg_price'],
                None,
                None
            ]
        }

        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name='EV & Hybrid', index=False, startrow=1)

        # Format
        worksheet = writer.sheets['EV & Hybrid']
        worksheet.write(0, 0, 'Electric & Hybrid Vehicle Analysis', header_format)
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:D', 15)

        # Add EV models list
        ev_cars = [c for c in analyzer.catalog if c.get('is_ev')]
        if ev_cars:
            start_row = 8
            worksheet.write(start_row, 0, 'Electric Vehicle Models', header_format)

            for i, car in enumerate(ev_cars):
                worksheet.write(start_row + 1 + i, 0, car.get('brand', ''))
                worksheet.write(start_row + 1 + i, 1, car.get('model', ''))
                if car.get('base_price_mxn'):
                    worksheet.write(start_row + 1 + i, 2, float(car['base_price_mxn']), money_format)


def generate_csv_exports(catalog_path: Optional[Path] = None) -> list[Path]:
    """
    Generate CSV exports from catalog data

    Returns:
        List of generated file paths
    """
    config = get_config()
    analyzer = NewCarAnalyzer(catalog_path)
    output_dir = config.output_path
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []

    # Full catalog CSV
    catalog_df = pd.DataFrame([
        {
            'brand': c.get('brand', ''),
            'model': c.get('model', ''),
            'year': c.get('year', ''),
            'body_type': c.get('body_type', ''),
            'base_price_mxn': float(c['base_price_mxn']) if c.get('base_price_mxn') else None,
            'price_bucket': c.get('price_bucket', ''),
            'transmission': c.get('transmission', ''),
            'fuel_type': c.get('fuel_type', ''),
            'origin_country': c.get('origin_country', ''),
            'is_ev': c.get('is_ev', False),
            'is_hybrid': c.get('is_hybrid', False),
        }
        for c in analyzer.catalog
    ])

    catalog_file = output_dir / f"new_cars_catalog_{date.today().isoformat()}.csv"
    catalog_df.to_csv(catalog_file, index=False)
    files.append(catalog_file)
    logger.info(f"Generated: {catalog_file}")

    # Brand summary CSV
    brand_df = pd.DataFrame([
        {
            'brand': s.brand,
            'model_count': s.model_count,
            'min_price_mxn': float(s.min_price),
            'max_price_mxn': float(s.max_price),
            'avg_price_mxn': float(s.avg_price),
            'median_price_mxn': float(s.median_price),
            'has_ev': s.has_ev,
            'has_hybrid': s.has_hybrid,
        }
        for s in analyzer.get_brand_stats()
    ])

    brand_file = output_dir / f"new_cars_by_brand_{date.today().isoformat()}.csv"
    brand_df.to_csv(brand_file, index=False)
    files.append(brand_file)
    logger.info(f"Generated: {brand_file}")

    # Segment summary CSV
    segment_df = pd.DataFrame([
        {
            'segment': s.segment,
            'segment_label': s.segment_label,
            'model_count': s.model_count,
            'brand_count': s.brand_count,
            'min_price_mxn': float(s.min_price),
            'max_price_mxn': float(s.max_price),
            'avg_price_mxn': float(s.avg_price),
        }
        for s in analyzer.get_segment_stats()
    ])

    segment_file = output_dir / f"new_cars_by_segment_{date.today().isoformat()}.csv"
    segment_df.to_csv(segment_file, index=False)
    files.append(segment_file)
    logger.info(f"Generated: {segment_file}")

    return files


def main():
    """Generate reports"""
    logging.basicConfig(level=logging.INFO)

    reporter = ExcelReporter()

    # Generate Excel report
    excel_path = reporter.generate_new_car_report()
    print(f"Generated Excel report: {excel_path}")

    # Generate CSV exports
    csv_files = generate_csv_exports()
    print(f"Generated {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
