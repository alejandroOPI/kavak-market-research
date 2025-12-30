# Data Sources Reference

Detailed documentation for all data sources used in KAVAK Market Research.

## New Car Data Sources

### Autocosmos Mexico

**URL**: https://www.autocosmos.com.mx/catalogo

**Description**: Comprehensive new car catalog for the Mexican market with MSRP prices.

**Data Available**:
- All brands sold in Mexico (65+)
- All models and versions/trims
- MSRP prices in MXN
- Basic specifications (engine, transmission, body type)
- Country of origin

**URL Patterns**:
```
/catalogo                          - Main catalog
/catalogo/vigente/{brand}          - Brand page
/catalogo/vigente/{brand}/{model}  - Model details
```

**Scraping Notes**:
- Rate limit: 1 request per second
- User-Agent should mimic browser
- Prices in format "$XXX,XXX"

**Data Quality**:
- Generally accurate MSRP prices
- Some model names have extra text
- Body type classification varies

---

### INEGI RAIAVL

**URL**: https://www.inegi.org.mx/datosprimarios/iavl/

**Description**: Official government registry of light vehicle industry data.

**Data Available**:
- Monthly production by brand
- Domestic sales (ventas al público)
- Export volumes by destination
- Data from 23 AMIA-affiliated companies

**NOT Available**:
- Prices (no monetary values)
- City-level breakdown (only national)

**API Access**:
```
Base: https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml
Format: /INDICATOR/{id}/{lang}/{area}/{recent}/{source}/{version}/{token}
```

**Registration**: https://www.inegi.org.mx/servicios/api_indicadores.html

**Key Indicators** (IDs may change):
- Light vehicle production
- Light vehicle domestic sales
- Light vehicle exports

---

### INEGI VMRC

**URL**: https://www.inegi.org.mx/programas/vehiculosmotor/

**Description**: Registered vehicles in circulation by state.

**Data Available**:
- Total registered vehicles by state
- Vehicle class (automobile, truck, motorcycle)
- Service type (private, public, official)
- Historical time series

**Geographic Granularity**: State level (32 states + CDMX)

---

### AMIA

**URL**: https://www.amia.com.mx/publicaciones/

**Description**: Mexican Automotive Industry Association bulletins.

**Data Available**:
- Monthly sales by brand
- Production by manufacturer
- Export destination breakdown
- EV/Hybrid segment data

**Format**: PDF and Excel bulletins (manual download)

---

## Used Car Data Sources

### KAVAK Internal API

**Status**: Pending configuration

**Expected Endpoints**:
```
/v1/inventory     - Current vehicle inventory
/v1/pricing       - Pricing data and history
/v1/sales         - Completed transactions
/v1/demand        - Views, leads, inquiries
```

**Required Fields**:
- Vehicle: brand, model, year, body_type, mileage
- Location: city, state, hub_id
- Pricing: list_price, purchase_price
- Timing: listing_date, sold_date, days_in_inventory
- Demand: page_views, leads_generated

---

## Supplementary Sources

### Libro Azul

**URL**: https://www.libroazul.com/

**Data**: Used car reference prices (Mexican Blue Book)

### Banco de México

**URL**: https://www.banxico.org.mx/

**Data**: Exchange rates, interest rates, inflation

### CONAPO

**URL**: https://www.gob.mx/conapo

**Data**: Population by city/state for market sizing
