---
name: market-research
description: This skill should be used when the user asks to "run market research", "generate market report", "collect car data", "analyze new car prices", "analyze used car market", "get INEGI data", "scrape Autocosmos", "monthly market report", "sales by state", "geographic analysis", or needs automotive market analysis for Mexico. Provides comprehensive market research capabilities for new and used cars.
version: 0.2.0
---

# KAVAK Market Research Skill

This skill provides automated market research capabilities for the Mexican automotive market, covering both new and used cars with geographic (state/city) breakdowns.

## Purpose

Generate monthly market research reports analyzing:
- New car prices and availability from Autocosmos
- Production and sales data from INEGI
- Vehicle registrations by state from INEGI VMRC
- EV/Hybrid sales estimates by state
- Used car inventory and pricing from KAVAK (when API configured)

## When to Use

Trigger this skill when:
- Running monthly market research collection
- Generating market analysis reports
- Comparing new vs used car prices
- Analyzing market by brand, segment, city, or price bucket
- Getting geographic/state-level vehicle data

## Quick Start

### Run Full Monthly Report

To generate a complete monthly market research report:

```bash
# Navigate to project
cd /Users/alejandro/kavak-market-research

# Activate environment
source venv/bin/activate

# Collect all data and generate reports
python -m src.main collect --source autocosmos
python -m src.collectors.inegi_pdf_parser  # Download INEGI bulletins
python scripts/collect_geographic_data.py   # Get state-level data
python -m src.analyzers.new_cars
python -m src.reporters.excel
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

### Collect Geographic/State Data

To get vehicle registrations and EV sales by state:

```bash
source venv/bin/activate
python scripts/collect_geographic_data.py
```

This downloads:
- VMRC annual data (vehicle registrations by state)
- VMRC monthly data (national production/sales)
- Generates EV/Hybrid sales estimates by state

### Generate Reports

To generate Excel, CSV, and text reports from collected data:

```bash
source venv/bin/activate
python -m src.reporters.excel
python -m src.analyzers.new_cars
```

## Data Sources

### New Cars (National)

| Source | Data | Status |
|--------|------|--------|
| Autocosmos | MSRP prices, all brands/models | Active |
| INEGI RAIAVL | Production, sales, exports | Active (PDF bulletins) |
| AMIA | Industry bulletins | Manual download |

### Geographic Data (By State)

| Source | Data | Status |
|--------|------|--------|
| INEGI VMRC | Vehicle registrations by state | Active |
| INEGI VMRC | Monthly national sales/production | Active |
| INEGI + Statista | EV/Hybrid sales by state | Estimated |

**Note**: State-level new car SALES data is not publicly available. We use:
- Vehicle registrations as market size proxy
- Estimated EV/Hybrid sales based on national totals and state distribution

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
| `vehicle_registrations_by_city_{date}.csv` | State-level registrations |

### Excel Workbook Sheets

1. **Summary** - Overview stats (models, brands, price range)
2. **By Brand** - Analysis by manufacturer
3. **By Segment** - Analysis by price tier
4. **Full Catalog** - All 600+ models with specs
5. **EV & Hybrid** - Electric/hybrid vehicle analysis
6. **By Geography** - State-level registrations and EV sales

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

### Geographic Coverage (12 Tier 1 Cities)

| City | State | Market Share |
|------|-------|--------------|
| Ciudad de Mexico | CDMX | 24.4% |
| Guadalajara | Jalisco | 17.4% |
| Monterrey | Nuevo Leon | 8.4% |
| Tijuana | Baja California | 9.1% |
| Leon | Guanajuato | 9.0% |
| Puebla | Puebla | 4.8% |
| Queretaro | Queretaro | 3.3% |
| Merida | Yucatan | 4.0% |
| Cancun | Quintana Roo | 4.0% |
| Cuernavaca | Morelos | 4.9% |
| Morelia | Michoacan | 7.8% |
| Aguascalientes | Aguascalientes | 2.9% |

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
│   │   └── excel.py            # Excel/CSV reports (incl. geographic)
│   └── processors/         # Data standardization
├── scripts/
│   ├── collect_geographic_data.py  # State-level data collection
│   └── scrape_inegi_ev_by_state.py # EV sales scraper
├── data/
│   ├── raw/
│   │   ├── inegi/             # INEGI PDF bulletins
│   │   │   └── vmrc/          # VMRC state-level data
│   │   └── autocosmos/        # Autocosmos JSON
│   ├── processed/         # Cleaned data
│   │   ├── city_vehicle_registrations_2023.json
│   │   ├── ev_sales_by_state_estimated.json
│   │   └── inegi_2025_summary.json
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

1. **Collect new car data** from Autocosmos (all 65+ brands)
2. **Download INEGI bulletins** for production/sales volumes
3. **Collect geographic data** - state-level registrations and EV estimates
4. **Pull KAVAK data** for used car metrics (when API available)
5. **Generate analysis** by brand, segment, body type, geography
6. **Create reports** in Excel, CSV, and text formats
7. **Compare periods** for MoM and YoY trends

### Ad-hoc Analysis

For specific questions:
- "What's the cheapest SUV from Toyota?" → Query the catalog
- "How many EV models are available?" → Run EV/Hybrid analysis
- "Compare Nissan vs Honda prices" → Generate brand comparison
- "Sales by state" → Check geographic sheet in Excel report
- "Which cities have most vehicles?" → vehicle_registrations_by_city CSV

## Scripts

### Main Scripts

- `src/main.py` - CLI entry point for data collection
- `src/analyzers/new_cars.py` - Market analysis
- `src/reporters/excel.py` - Report generation (all sheets)

### Data Collection Scripts

- `scripts/collect_geographic_data.py` - Download VMRC and generate state estimates
- `scripts/scrape_inegi_ev_by_state.py` - Attempt to scrape INEGI interactive data

## Data Availability Notes

### What's Publicly Available

| Data | Source | Granularity | Available |
|------|--------|-------------|-----------|
| New car MSRP | Autocosmos | National | Yes |
| Production | INEGI RAIAVL | National | Yes |
| Sales | INEGI RAIAVL | National | Yes |
| Exports | INEGI RAIAVL | National | Yes |
| Vehicle Registrations | INEGI VMRC | By State | Yes |
| EV/Hybrid Sales | INEGI RAIAVL | By State | Interactive only |

### What's NOT Publicly Available

- **New car sales by state** - Only national totals from INEGI/AMIA
- **AMIA member data** - Requires membership
- **Dealer-level data** - Proprietary

### Workarounds

1. **State market size**: Use VMRC registrations as proxy
2. **EV sales by state**: Estimate from national totals + known state distribution
3. **City-level data**: Will come from KAVAK API for used cars

## Troubleshooting

### No data collected

- Check internet connection
- Verify Autocosmos website is accessible
- Check rate limiting (1 request/second)

### INEGI downloads fail

- INEGI requires browser-like headers
- Check if PDF bulletin URLs have changed
- Try downloading manually from inegi.org.mx

### Geographic data missing

- Run `python scripts/collect_geographic_data.py`
- Check `data/raw/inegi/vmrc/` for downloaded files
- Check `data/processed/` for generated JSON files

### Reports not generating

- Ensure data exists in `data/raw/autocosmos/`
- Check Python dependencies: `pip install -r requirements.txt`
- Verify processed data files exist
