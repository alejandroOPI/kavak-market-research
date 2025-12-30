---
name: market-research
description: This skill should be used when the user asks to "run market research", "generate market report", "collect car data", "analyze new car prices", "analyze used car market", "get INEGI data", "scrape Autocosmos", "monthly market report", or needs automotive market analysis for Mexico. Provides comprehensive market research capabilities for new and used cars.
version: 0.1.0
---

# KAVAK Market Research Skill

This skill provides automated market research capabilities for the Mexican automotive market, covering both new and used cars.

## Purpose

Generate monthly market research reports analyzing:
- New car prices and availability from Autocosmos
- Production and sales data from INEGI
- Used car inventory and pricing from KAVAK (when API configured)

## When to Use

Trigger this skill when:
- Running monthly market research collection
- Generating market analysis reports
- Comparing new vs used car prices
- Analyzing market by brand, segment, city, or price bucket

## Quick Start

### Run Full Monthly Report

To generate a complete monthly market research report:

```bash
# Navigate to project
cd /Users/alejandro/kavak-market-research

# Activate environment
source venv/bin/activate

# Collect data and generate reports
python scripts/run_monthly.py --month 2025-01
```

### Collect New Car Data Only

To scrape current new car prices from Autocosmos:

```bash
source venv/bin/activate
python -m src.main collect --source autocosmos
```

For specific brands only:

```bash
python -m src.main collect --source autocosmos --brands nissan,toyota,honda,chevrolet
```

### Generate Reports

To generate Excel, CSV, and text reports from collected data:

```bash
source venv/bin/activate
python -m src.reporters.excel
python -m src.analyzers.new_cars
```

## Data Sources

### New Cars

| Source | Data | Status |
|--------|------|--------|
| Autocosmos | MSRP prices, all brands/models | ✅ Active |
| INEGI RAIAVL | Production, sales, exports | ✅ Active (PDF bulletins) |
| AMIA | Industry bulletins | Manual download |

### Used Cars

| Source | Data | Status |
|--------|------|--------|
| KAVAK API | Inventory, pricing, sales | Pending API config |

## Report Outputs

Reports are saved to `data/outputs/`:

| File | Description |
|------|-------------|
| `kavak_new_cars_{date}.xlsx` | Excel workbook with multiple sheets |
| `new_car_report_{date}.txt` | Text summary report |
| `new_cars_catalog_{date}.csv` | Full catalog CSV |
| `new_cars_by_brand_{date}.csv` | Brand summary CSV |
| `new_cars_by_segment_{date}.csv` | Segment summary CSV |

## Analysis Dimensions

### Price Segments

| Segment | Range (MXN) |
|---------|-------------|
| Entry | < $150,000 |
| Economy | $150,000 - $300,000 |
| Mid-Range | $300,000 - $500,000 |
| Premium | $500,000 - $800,000 |
| Luxury | $800,000 - $1,200,000 |
| Ultra | > $1,200,000 |

### Geographic Coverage (Tier 1 Cities)

Ciudad de México, Guadalajara, Monterrey, Puebla, Querétaro, León, Mérida, Tijuana, Aguascalientes, Cancún, Cuernavaca, Morelia

### Brand Tiers

- **Volume**: Nissan, Chevrolet, VW, Toyota, Honda, Kia, Hyundai, Mazda
- **Premium**: BMW, Mercedes-Benz, Audi, Volvo
- **Luxury**: Porsche, Land Rover, Lexus

## Project Structure

```
kavak-market-research/
├── src/
│   ├── collectors/         # Data collection
│   │   ├── autocosmos.py       # New car prices scraper
│   │   ├── inegi.py            # INEGI data collector
│   │   └── inegi_pdf_parser.py # INEGI PDF bulletin parser
│   ├── analyzers/          # Analysis modules
│   │   └── new_cars.py         # New car analysis
│   ├── reporters/          # Report generation
│   │   └── excel.py            # Excel/CSV reports
│   └── processors/         # Data standardization
├── data/
│   ├── raw/               # Raw collected data
│   │   ├── inegi/             # INEGI PDF bulletins
│   │   └── autocosmos/        # Autocosmos JSON
│   ├── processed/         # Cleaned data
│   └── outputs/           # Generated reports
├── config/
│   └── settings.yaml      # Configuration
└── skills/                # This skill
```

## Configuration

Copy and edit the configuration file:

```bash
cp config/settings.example.yaml config/settings.yaml
```

Key settings:
- `sources.inegi.api_token`: INEGI API token (register at inegi.org.mx)
- `sources.kavak.api.base_url`: KAVAK API endpoint
- `sources.kavak.api.api_key`: KAVAK API key

## Workflow

### Monthly Research Workflow

1. **Collect new car data** from Autocosmos (all brands or top 10)
2. **Fetch INEGI data** for production/sales volumes (if API configured)
3. **Pull KAVAK data** for used car metrics (when API available)
4. **Generate analysis** by brand, segment, body type
5. **Create reports** in Excel, CSV, and text formats
6. **Compare periods** for MoM and YoY trends

### Ad-hoc Analysis

For specific questions:
- "What's the cheapest SUV from Toyota?" → Query the catalog
- "How many EV models are available?" → Run EV/Hybrid analysis
- "Compare Nissan vs Honda prices" → Generate brand comparison

## Scripts

### Main Scripts

- `src/main.py` - CLI entry point for data collection
- `src/analyzers/new_cars.py` - Market analysis
- `src/reporters/excel.py` - Report generation

### Skill Scripts

- `scripts/run_monthly.py` - Full monthly workflow
- `scripts/quick_report.sh` - Quick report generation

## Additional Resources

### Reference Files

- **`references/data-sources.md`** - Detailed data source documentation
- **`references/analysis-guide.md`** - Analysis methodology

### Example Outputs

- **`examples/sample_report.txt`** - Sample text report
- **`examples/brand_analysis.csv`** - Sample brand CSV

## Common Tasks

### Add New Brand to Analysis

Brands are auto-discovered from Autocosmos. To filter specific brands:

```bash
python -m src.main collect --source autocosmos --brands brand1,brand2
```

### Update Price Buckets

Edit `config/settings.yaml` under `price_buckets` section.

### Add New City

Edit `config/settings.yaml` under `geography.tier1_cities` or `tier2_cities`.

## Troubleshooting

### No data collected

- Check internet connection
- Verify Autocosmos website is accessible
- Check rate limiting (1 request/second)

### INEGI API fails

- Register for API token at https://www.inegi.org.mx/servicios/api_indicadores.html
- Set `INEGI_API_TOKEN` environment variable or in settings.yaml

### Reports not generating

- Ensure data exists in `data/raw/autocosmos/`
- Check Python dependencies: `pip install -r requirements.txt`
