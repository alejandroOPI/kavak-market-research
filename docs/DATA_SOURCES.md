# Data Sources Documentation

## 1. New Cars - Official Government Sources

### 1.1 INEGI - RAIAVL (Registro Administrativo de la Industria Automotriz de Vehículos Ligeros)

**URL**: https://www.inegi.org.mx/datosprimarios/iavl/

**Description**: Monthly data on light vehicle production, sales, and exports from 23 AMIA-affiliated companies covering 37 brands.

**Data Available**:
- Monthly production by brand/model
- Domestic sales (ventas al público)
- Export volumes by destination
- Data by company/manufacturer

**Data NOT Available**:
- Prices (no monetary values)
- Geographic breakdown by state/city for sales

**Update Frequency**: Monthly (released ~4-6 weeks after month end)

**Access Method**:
- Direct CSV/Excel downloads
- API: https://www.inegi.org.mx/servicios/api.html

**Key Metrics 2024**:
- Total production: 3,989,403 units (+5.6% YoY)
- Total exports: 3,479,086 units (+5.4% YoY)
- US share of exports: 79.7%

---

### 1.2 INEGI - VMRC (Vehículos de Motor Registrados en Circulación)

**URL**: https://www.inegi.org.mx/programas/vehiculosmotor/

**Description**: Monthly statistics on the total registered vehicle fleet circulating in Mexico.

**Data Available**:
- Total vehicles registered by state
- Vehicle class (automobile, truck, motorcycle)
- Service type (private, public, official)
- Historical time series

**Geographic Granularity**: State level (entidad federativa)

**Update Frequency**: Monthly

**Key Metrics 2024**:
- Total registered automobiles: 37.8 million (as of Nov 2024)
- YoY growth: +1.8%

---

### 1.3 AMIA (Asociación Mexicana de la Industria Automotriz)

**URL**: https://www.amia.com.mx/publicaciones/

**Description**: Industry association representing automakers in Mexico. Publishes monthly sales, production, and export bulletins.

**Data Available**:
- Monthly sales by brand
- Production by manufacturer
- Export data
- Hybrid/EV sales breakdowns

**Access Method**: PDF/Excel reports on website

**Notable 2024 Stats**:
- Record year for production and exports
- Production: 3.99M units (beat 2017 record)

---

### 1.4 AMDA (Asociación Mexicana de Distribuidores de Automotores)

**URL**: https://www.amda.mx/

**Description**: Association of automotive dealers in Mexico.

**Data Available**:
- Dealer-level sales data
- Used car transaction data (limited)
- Financing trends

---

## 2. Used Cars - KAVAK Internal Data

### 2.1 Required Data Feeds

| Feed Name | Description | Frequency | Priority |
|-----------|-------------|-----------|----------|
| `inventory_snapshot` | Current vehicles in inventory | Daily | Critical |
| `pricing_history` | Price changes over time | Daily | Critical |
| `sales_transactions` | Completed sales | Daily | Critical |
| `demand_metrics` | Views, leads, inquiries | Daily | High |
| `acquisition_data` | Purchase prices, sources | Weekly | Medium |

### 2.2 Required Schema

```json
{
  "vehicle": {
    "internal_id": "string",
    "vin": "string (optional)",
    "brand": "string",
    "model": "string",
    "year": "integer",
    "body_type": "enum (sedan|suv|pickup|hatchback|van|coupe)",
    "transmission": "enum (automatic|manual)",
    "fuel_type": "enum (gasoline|diesel|hybrid|electric)",
    "mileage_km": "integer",
    "color": "string",
    "trim": "string"
  },
  "location": {
    "city": "string",
    "state": "string",
    "hub_id": "string",
    "hub_name": "string"
  },
  "pricing": {
    "list_price_mxn": "decimal",
    "purchase_price_mxn": "decimal (if available)",
    "price_history": [
      {"date": "date", "price": "decimal"}
    ]
  },
  "timing": {
    "acquisition_date": "date",
    "listing_date": "date",
    "sold_date": "date (if sold)",
    "days_in_inventory": "integer"
  },
  "demand": {
    "page_views": "integer",
    "leads_generated": "integer",
    "test_drives_scheduled": "integer",
    "inquiries": "integer"
  },
  "status": "enum (available|reserved|sold|in_transit)"
}
```

### 2.3 Data Delivery Options

**Option A: Database Access**
- Direct read-only access to KAVAK data warehouse
- Real-time or near-real-time data
- Requires VPN/credentials setup

**Option B: API Endpoint**
- REST API with authentication
- Paginated responses
- Rate limited

**Option C: Scheduled Exports**
- Daily/weekly CSV/JSON exports
- Delivered to S3 bucket or SFTP
- Simplest to implement

---

## 3. Supplementary Data Sources

### 3.1 Pricing Reference - Libro Azul

**URL**: https://www.libroazul.com/

**Data**: Reference prices for used vehicles in Mexico

### 3.2 Economic Data - Banco de México

**URL**: https://www.banxico.org.mx/

**Data**:
- Exchange rates (USD/MXN)
- Interest rates (for financing context)
- Inflation data

### 3.3 Population Data - CONAPO

**URL**: https://www.gob.mx/conapo

**Data**:
- Population by city/state
- Demographic projections

---

## 4. Data Quality Considerations

### Standardization Needed

| Field | Issue | Solution |
|-------|-------|----------|
| City names | Different spellings | Canonical mapping table |
| Brand names | Inconsistent casing | Brand master list |
| Body types | Various classifications | Standard taxonomy |
| Price buckets | Different ranges | Unified bucket definitions |

### Data Gaps to Address

1. **New car prices**: INEGI doesn't provide prices, need AMIA/AMDA or third-party
2. **City-level new car sales**: Only state-level from official sources
3. **Used car market size (non-KAVAK)**: May need third-party data

---

## 5. API Integration Notes

### INEGI API

```bash
# Example API call for vehicle registration data
curl "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{indicator_id}/es/0700/false/BISE/2.0/{token}?type=json"
```

Register for API token at: https://www.inegi.org.mx/servicios/api.html

### Common Indicators
- Producción de vehículos ligeros
- Ventas de vehículos ligeros
- Exportación de vehículos ligeros
