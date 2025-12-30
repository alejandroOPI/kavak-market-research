# Market Research System - Implementation Plan

## Phase 1: Data Source Setup

### 1.1 New Cars - Official Sources (INEGI + Others)

**INEGI Data Available:**
- Registro Administrativo de la Industria Automotriz de Vehículos Ligeros
- URL: https://www.inegi.org.mx/temas/vehiculos/
- Data: Monthly new vehicle registrations by state, brand, vehicle type
- Format: CSV/XLSX downloads or API

**AMIA (Asociación Mexicana de la Industria Automotriz):**
- URL: https://www.amia.com.mx/
- Data: Production, exports, domestic sales
- Format: Monthly bulletins (PDF/Excel)

**AMDA (Asociación Mexicana de Distribuidores de Automotores):**
- URL: https://www.amda.mx/
- Data: Dealer-level sales data
- Format: Monthly reports

**Data Points to Extract:**
- [ ] Total new car sales by month
- [ ] Sales by state/city
- [ ] Sales by brand
- [ ] Sales by vehicle type (sedan, SUV, pickup, etc.)
- [ ] Average prices (if available)

### 1.2 Used Cars - KAVAK Internal Data

**Required Data Feeds (to be provided):**
- Inventory snapshots (daily/weekly)
- Pricing data (listing prices, changes)
- Sales transactions
- Demand metrics (views, leads, conversions)

**Required Fields:**
```yaml
vehicle:
  - vin or internal_id
  - brand
  - model
  - year
  - body_type (sedan, suv, pickup, etc.)
  - transmission
  - fuel_type
  - mileage

location:
  - city
  - state
  - hub_id

pricing:
  - list_price
  - purchase_price
  - price_history[]

timing:
  - inventory_date
  - sold_date
  - days_in_inventory

demand:
  - page_views
  - leads_generated
  - test_drives
```

---

## Phase 2: Segmentation Schema

### 2.1 Geographic Segmentation

**Cities (Tier 1 - Major Markets):**
| City | State | Code |
|------|-------|------|
| Ciudad de México | CDMX | MX-CMX |
| Guadalajara | Jalisco | MX-JAL |
| Monterrey | Nuevo León | MX-NLE |
| Puebla | Puebla | MX-PUE |
| Querétaro | Querétaro | MX-QUE |
| León | Guanajuato | MX-GUA |
| Mérida | Yucatán | MX-YUC |
| Tijuana | Baja California | MX-BCN |

**Cities (Tier 2 - Growth Markets):**
- Aguascalientes, San Luis Potosí, Toluca, Cancún, etc.

### 2.2 Price Buckets

| Bucket | Range (MXN) | Target Segment |
|--------|-------------|----------------|
| Entry | < 150,000 | Budget buyers |
| Economy | 150,000 - 300,000 | First-time buyers |
| Mid-Range | 300,000 - 500,000 | Family segment |
| Premium | 500,000 - 800,000 | Premium segment |
| Luxury | 800,000 - 1,200,000 | Luxury entry |
| Ultra | > 1,200,000 | Luxury high-end |

### 2.3 Vehicle Types

| Type | Examples |
|------|----------|
| Sedan | Versa, Jetta, Civic |
| SUV Compact | HR-V, CX-30, Kicks |
| SUV Mid | CR-V, RAV4, Tiguan |
| SUV Full | Pilot, Tahoe, Durango |
| Pickup | Hilux, Ranger, Colorado |
| Hatchback | Polo, Fit, Mazda 2 |
| Van/Minivan | Sienna, Odyssey |
| Coupe/Sports | Mustang, Camaro |

### 2.4 Brands & Tiers

**Volume Brands:**
- Nissan, Chevrolet, Volkswagen, Toyota, Honda, Kia, Hyundai, Mazda

**Premium Brands:**
- BMW, Mercedes-Benz, Audi, Volvo

**Luxury Brands:**
- Porsche, Land Rover, Lexus

---

## Phase 3: Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   INEGI      │   │    AMIA      │   │   KAVAK      │    │
│  │  (Monthly)   │   │  (Monthly)   │   │  (Weekly)    │    │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘    │
│         │                  │                  │            │
│         ▼                  ▼                  ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              RAW DATA STORAGE                       │   │
│  │          (data/raw/{source}/{date}/)                │   │
│  └─────────────────────────┬───────────────────────────┘   │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│                    DATA PROCESSING                          │
├────────────────────────────┼────────────────────────────────┤
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              STANDARDIZATION                        │   │
│  │  - Normalize city/state names                       │   │
│  │  - Map brand/model to canonical names               │   │
│  │  - Classify vehicle types                           │   │
│  │  - Assign price buckets                             │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AGGREGATION                            │   │
│  │  - Group by dimensions                              │   │
│  │  - Calculate metrics                                │   │
│  │  - Compute YoY/MoM changes                          │   │
│  └─────────────────────────┬───────────────────────────┘   │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│                    OUTPUT GENERATION                        │
├────────────────────────────┼────────────────────────────────┤
│                            ▼                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │    Excel     │  │     PDF      │      │
│  │   (JSON)     │  │   Reports    │  │   Summary    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 4: Key Metrics & KPIs

### Market Metrics (New + Used Combined)
- Total addressable market (TAM) by city
- Market share by brand
- Average selling price by segment
- Volume growth rates (MoM, YoY)

### KAVAK-Specific Metrics
- Inventory turnover by city/segment
- Price competitiveness (vs. market avg)
- Days to sale by segment
- Demand-supply gap by category
- Conversion funnel metrics

### Comparative Metrics
- Used/New price ratio by model
- Used car market penetration vs. new
- Price depreciation curves

---

## Phase 5: Implementation Timeline

### Week 1-2: Foundation
- [x] Create repository
- [ ] Set up project structure
- [ ] Define data schemas
- [ ] Create configuration system

### Week 3-4: Data Collection
- [ ] Build INEGI data collector
- [ ] Build AMIA/AMDA data collector
- [ ] Integrate KAVAK data feeds
- [ ] Create data validation layer

### Week 5-6: Processing & Analysis
- [ ] Build data standardization pipeline
- [ ] Create aggregation modules
- [ ] Implement metric calculations
- [ ] Build comparison logic

### Week 7-8: Reporting & Automation
- [ ] Create report templates
- [ ] Build visualization components
- [ ] Create Claude Code skill
- [ ] Set up monthly automation
- [ ] Documentation

---

## Phase 6: Claude Code Skill

The skill will be installed as a Claude Code plugin for easy monthly execution:

```bash
/market-research run --month 2025-01
/market-research compare --months 2024-12,2025-01
/market-research city --city guadalajara --month 2025-01
```

**Skill Capabilities:**
1. Fetch latest data from all sources
2. Process and aggregate
3. Generate reports
4. Compare periods
5. Answer ad-hoc questions about the data

---

## Questions for Review

1. **Data Access**: How will KAVAK internal data be provided?
   - Direct database access?
   - API endpoint?
   - Scheduled data exports?

2. **Cities**: Which cities should be included in Tier 1 vs Tier 2?

3. **Price Buckets**: Are the proposed ranges appropriate for KAVAK's market?

4. **Report Format**: Preferred output format?
   - Excel with multiple sheets?
   - Interactive dashboard?
   - PDF summary?

5. **Frequency**: Monthly is mentioned, but do you need weekly quick updates?

6. **Historical Data**: How far back should we go for trend analysis?
