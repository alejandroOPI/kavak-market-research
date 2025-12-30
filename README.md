# KAVAK Market Research

Monthly market research for new and used cars in Mexico - segmented by city, price bucket, car type, and brand.

## Overview

This system aggregates and analyzes automotive market data from two primary sources:

1. **New Cars**: INEGI and official government sources
2. **Used Cars**: KAVAK internal data

## Segmentation Dimensions

| Dimension | Description |
|-----------|-------------|
| City | Major Mexican cities (CDMX, Guadalajara, Monterrey, etc.) |
| Price Bucket | Ranges like <150k, 150-300k, 300-500k, 500k-1M, >1M MXN |
| Car Type | Sedan, SUV, Pickup, Hatchback, Coupe, Van |
| Brand | Toyota, Nissan, VW, Honda, Chevrolet, etc. |
| Model Year | New vs 1-3 years vs 4-6 years vs 7+ years |

## Project Structure

```
kavak-market-research/
├── data/
│   ├── raw/              # Raw data from sources
│   │   ├── inegi/        # INEGI data
│   │   └── kavak/        # KAVAK internal data
│   ├── processed/        # Cleaned and transformed data
│   └── outputs/          # Final reports and analysis
├── src/
│   ├── collectors/       # Data collection scripts
│   │   ├── inegi.py      # INEGI API/scraper
│   │   └── kavak.py      # KAVAK data connector
│   ├── processors/       # Data transformation
│   ├── analyzers/        # Analysis modules
│   └── reporters/        # Report generation
├── config/
│   └── settings.yaml     # Configuration
├── skills/               # Claude Code skill for monthly execution
└── notebooks/            # Exploratory analysis
```

## Data Sources

### 1. New Cars (Official Sources)

| Source | Data Available | Update Frequency |
|--------|---------------|------------------|
| INEGI - Registro de Vehículos | New car registrations by state, brand, type | Monthly |
| AMIA (Asociación Mexicana de la Industria Automotriz) | Production and sales data | Monthly |
| AMDA (Asociación Mexicana de Distribuidores de Automotores) | Dealer sales data | Monthly |

### 2. Used Cars (KAVAK Sources)

| Data Type | Description |
|-----------|-------------|
| Inventory | Current cars available by location |
| Pricing | Listing prices, price changes over time |
| Sales | Sold vehicles, time-to-sale |
| Demand | Views, inquiries, conversion rates |

## Monthly Report Output

The system generates:

1. **Market Overview**: Total market size, growth trends
2. **City Analysis**: Per-city breakdown with YoY comparisons
3. **Price Analysis**: Price trends by segment
4. **Brand Performance**: Market share by brand
5. **Inventory Health**: KAVAK-specific metrics

## Setup

```bash
pip install -r requirements.txt
cp config/settings.example.yaml config/settings.yaml
# Configure your API keys and data sources
```

## Usage

```bash
# Run monthly report
python -m src.main --month 2025-01

# Or use Claude Code skill
/market-research --month 2025-01
```
