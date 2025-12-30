# Sample Market Research Output

Example output from a market research run on December 30, 2025.

## Text Report Sample

```
======================================================================
KAVAK MARKET RESEARCH - NEW CAR ANALYSIS
Report Date: 2025-12-30
======================================================================

MARKET OVERVIEW
----------------------------------------
Total Models Analyzed: 137
Total Brands: 8
Price Range: $280,500 - $4,052,400 MXN
Average Price: $772,755 MXN
Median Price: $619,600 MXN

ANALYSIS BY BRAND
----------------------------------------
Brand             Models    Min Price    Max Price    Avg Price
------------------------------------------------------------
Chevrolet             29 $      307k $     4052k $     1060k [EV] [HYB]
Toyota                24 $      320k $     1710k $      763k [EV] [HYB]
Volkswagen            19 $      335k $     1199k $      667k
Nissan                16 $      292k $     1378k $      657k

ANALYSIS BY PRICE SEGMENT
----------------------------------------

Economy ($150k-$300k)
  Models: 3 from 2 brands
  Price Range: $280,500 - $297,700
  Brands: Hyundai, Nissan
  Top Models:
    - Hyundai Grand I10 Sedan: $297,700
    - Nissan March: $291,900
    - Hyundai Grand I10: $280,500

Mid-Range ($300k-$500k)
  Models: 44 from 8 brands
  Price Range: $301,900 - $499,900

ELECTRIC & HYBRID VEHICLES
----------------------------------------
Electric Vehicles: 17 models (12.4%)
  Average EV Price: $951,765 MXN
  Brands with EVs: Chevrolet, Toyota, Kia

Hybrid Vehicles: 16 models (11.7%)
  Average Hybrid Price: $900,412 MXN
```

## CSV Output Sample

### Brand Summary (new_cars_by_brand.csv)

```csv
brand,model_count,min_price_mxn,max_price_mxn,avg_price_mxn,median_price_mxn,has_ev,has_hybrid
Chevrolet,29,307400.0,4052400.0,1059879.0,913400.0,True,True
Toyota,24,320500.0,1710000.0,762770.0,622750.0,True,True
Volkswagen,19,335490.0,1199000.0,667245.0,640700.0,False,False
Nissan,16,291900.0,1377900.0,656775.0,518400.0,False,False
```

### Catalog Sample (new_cars_catalog.csv)

```csv
brand,model,year,body_type,base_price_mxn,price_bucket,transmission,fuel_type,origin_country,is_ev,is_hybrid
Chevrolet,Aveo,2026,sedan,320900.0,mid_range,manual,gasoline,Imported,False,False
Toyota,Corolla,2025,sedan,447000.0,mid_range,automatic,gasoline,Mexico,False,False
Nissan,Versa,2025,sedan,362900.0,mid_range,manual,gasoline,Mexico,False,False
```

## Excel Workbook Sheets

The generated Excel workbook contains:

1. **Summary** - Overall market metrics
2. **By Brand** - Statistics per brand (model count, price range, EV/hybrid flags)
3. **By Segment** - Price segment breakdown (entry through ultra-luxury)
4. **Full Catalog** - All models with filters
5. **EV & Hybrid** - Electric and hybrid vehicle analysis

## Key Insights from Sample Run

1. **Chevrolet leads in model count** with 29 models, followed by Toyota (24)
2. **Wide price range** from entry-level Hyundai Grand i10 ($280k) to Corvette Z06 ($4M)
3. **Mid-range dominates** with 44 models (32% of catalog)
4. **EV adoption growing** at 12.4% of models, averaging $952k
5. **Mexican production** present across major brands (Toyota, Chevrolet, Nissan)
