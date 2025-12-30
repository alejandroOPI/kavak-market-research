#!/usr/bin/env python3
"""
Collect geographic (state-level) vehicle data from INEGI VMRC

Downloads:
- Annual vehicle registrations by state/municipality
- Monthly national sales/production data
- Generates EV/Hybrid sales estimates by state

Usage:
    python scripts/collect_geographic_data.py
"""
import json
import logging
import os
import zipfile
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Output paths
RAW_DIR = Path("data/raw/inegi/vmrc")
PROCESSED_DIR = Path("data/processed")

# INEGI VMRC download URLs
VMRC_ANNUAL_URL = "https://www.inegi.org.mx/contenidos/programas/vehiculosmotor/datosabiertos/vmrc_anual_csv.zip"
VMRC_MONTHLY_URL = "https://www.inegi.org.mx/contenidos/programas/vehiculosmotor/datosabiertos/vmrc_mensual_csv.zip"

# Target cities and their states
CITY_STATE_MAP = {
    "Ciudad de México": "Ciudad de México",
    "Guadalajara": "Jalisco",
    "Monterrey": "Nuevo León",
    "Puebla": "Puebla",
    "Querétaro": "Querétaro",
    "León": "Guanajuato",
    "Mérida": "Yucatán",
    "Tijuana": "Baja California",
    "Aguascalientes": "Aguascalientes",
    "Cancún": "Quintana Roo",
    "Cuernavaca": "Morelos",
    "Morelia": "Michoacán de Ocampo",
}

# EV/Hybrid state distribution (based on Statista + market research)
STATE_EV_SHARE = {
    "Ciudad de México": 0.254,
    "Estado de México": 0.136,
    "Nuevo León": 0.095,
    "Jalisco": 0.090,
    "Guanajuato": 0.045,
    "Puebla": 0.035,
    "Querétaro": 0.038,
    "Baja California": 0.032,
    "Yucatán": 0.025,
    "Quintana Roo": 0.022,
    "Morelos": 0.020,
    "Michoacán de Ocampo": 0.018,
    "Aguascalientes": 0.015,
}

# National EV/Hybrid sales (from INEGI/Statista)
NATIONAL_EV_SALES = {
    "2020": 28456,
    "2021": 38915,
    "2022": 57834,
    "2023": 73680,
    "2024": 95000,  # Estimated
}


def download_vmrc_data():
    """Download VMRC annual and monthly data from INEGI"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/zip,application/octet-stream,*/*",
    }

    # Download annual data
    logger.info("Downloading VMRC annual data...")
    annual_zip = RAW_DIR / "vmrc_anual_csv.zip"
    try:
        resp = requests.get(VMRC_ANNUAL_URL, headers=headers, timeout=120)
        resp.raise_for_status()
        with open(annual_zip, 'wb') as f:
            f.write(resp.content)
        logger.info(f"Downloaded {annual_zip}")

        # Extract
        with zipfile.ZipFile(annual_zip, 'r') as zf:
            zf.extractall(RAW_DIR)
        logger.info("Extracted annual data")
    except Exception as e:
        logger.error(f"Failed to download annual data: {e}")

    # Download monthly data
    logger.info("Downloading VMRC monthly data...")
    monthly_zip = RAW_DIR / "vmrc_mensual_csv.zip"
    try:
        resp = requests.get(VMRC_MONTHLY_URL, headers=headers, timeout=120)
        resp.raise_for_status()
        with open(monthly_zip, 'wb') as f:
            f.write(resp.content)
        logger.info(f"Downloaded {monthly_zip}")

        # Extract
        monthly_dir = RAW_DIR / "mensual"
        monthly_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(monthly_zip, 'r') as zf:
            zf.extractall(monthly_dir)
        logger.info("Extracted monthly data")
    except Exception as e:
        logger.error(f"Failed to download monthly data: {e}")


def process_state_registrations():
    """Process VMRC data to get vehicle registrations by state"""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Find latest annual data file
    annual_dir = RAW_DIR / "conjunto_de_datos"
    if not annual_dir.exists():
        logger.warning("Annual data directory not found")
        return None

    # Get latest year file
    annual_files = sorted(annual_dir.glob("vmrc_anual_tr_cifra_*.csv"))
    if not annual_files:
        logger.warning("No annual data files found")
        return None

    latest_file = annual_files[-1]
    year = latest_file.stem.split("_")[-1]
    logger.info(f"Processing {latest_file.name} (year {year})")

    # Load state catalog
    states_file = RAW_DIR / "catalogos" / "tc_entidad.csv"
    if not states_file.exists():
        logger.warning("State catalog not found")
        return None

    states = pd.read_csv(states_file)
    states['ID_ENTIDAD'] = states['ID_ENTIDAD'].astype(str).str.strip()

    # Load annual data
    df = pd.read_csv(latest_file)
    df['ID_ENTIDAD'] = df['ID_ENTIDAD'].astype(str).str.strip()

    # Calculate totals
    df['TOTAL_AUTOS'] = df['AUTO_OFICIAL'] + df['AUTO_PUBLICO'] + df['AUTO_PARTICULAR']
    df['TOTAL_TRUCKS'] = df['CYC_CARGA_OFICIAL'] + df['CYC_CARGA_PUBLICO'] + df['CYC_CARGA_PARTICULAR']
    df['TOTAL_MOTOS'] = df['MOTO_OFICIAL'] + df['MOTO_DE_ALQUILER'] + df['MOTO_PARTICULAR']
    df['TOTAL_VEHICLES'] = df['TOTAL_AUTOS'] + df['TOTAL_TRUCKS'] + df['TOTAL_MOTOS']

    # Aggregate by state
    state_totals = df.groupby('ID_ENTIDAD').agg({
        'TOTAL_AUTOS': 'sum',
        'TOTAL_TRUCKS': 'sum',
        'TOTAL_MOTOS': 'sum',
        'TOTAL_VEHICLES': 'sum'
    }).reset_index()

    state_totals = state_totals.merge(states, on='ID_ENTIDAD', how='left')

    # Build city-level data
    city_data = []
    for city, state in CITY_STATE_MAP.items():
        state_row = state_totals[state_totals['NOM_ENTIDAD'] == state]
        if not state_row.empty:
            city_data.append({
                "city": city,
                "state": state,
                "total_autos": int(state_row['TOTAL_AUTOS'].values[0]),
                "total_trucks": int(state_row['TOTAL_TRUCKS'].values[0]),
                "total_motos": int(state_row['TOTAL_MOTOS'].values[0]),
                "total_vehicles": int(state_row['TOTAL_VEHICLES'].values[0])
            })

    # Sort by total vehicles
    city_data.sort(key=lambda x: x['total_vehicles'], reverse=True)

    # Calculate market share
    total = sum(c['total_vehicles'] for c in city_data)
    for c in city_data:
        c['market_share_pct'] = round(c['total_vehicles'] / total * 100, 1)

    # Save
    output_file = PROCESSED_DIR / f"city_vehicle_registrations_{year}.json"
    with open(output_file, 'w') as f:
        json.dump(city_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved registrations to {output_file}")
    return city_data


def generate_ev_estimates():
    """Generate EV/Hybrid sales estimates by state"""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Load registration data for reference
    reg_file = list(PROCESSED_DIR.glob("city_vehicle_registrations_*.json"))
    reg_data = []
    if reg_file:
        with open(reg_file[-1]) as f:
            reg_data = json.load(f)

    # Build state-level EV estimates
    state_ev_data = []
    for city, state in CITY_STATE_MAP.items():
        share = STATE_EV_SHARE.get(state, 0.01)

        ev_sales_by_year = {}
        for year, total in NATIONAL_EV_SALES.items():
            ev_sales_by_year[year] = int(total * share)

        # Get registration data
        reg_info = next((r for r in reg_data if r.get("city") == city), None)

        state_ev_data.append({
            "city": city,
            "state": state,
            "ev_hybrid_share_pct": round(share * 100, 1),
            "estimated_ev_sales_2023": ev_sales_by_year.get("2023", 0),
            "estimated_ev_sales_2024": ev_sales_by_year.get("2024", 0),
            "total_vehicle_registrations": reg_info["total_vehicles"] if reg_info else 0,
            "annual_ev_sales": ev_sales_by_year
        })

    # Sort by EV sales
    state_ev_data.sort(key=lambda x: x["estimated_ev_sales_2023"], reverse=True)

    # Save
    output = {
        "source": "Estimated from INEGI RAIAVL + Statista + VMRC data",
        "description": "Estimated EV/Hybrid vehicle sales by state/city",
        "methodology": "Based on known national totals from INEGI and state distribution from Statista",
        "national_totals": NATIONAL_EV_SALES,
        "by_city_state": state_ev_data,
        "data_quality": "Estimated - actual state-level sales data is not publicly available",
    }

    output_file = PROCESSED_DIR / "ev_sales_by_state_estimated.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved EV estimates to {output_file}")
    return state_ev_data


def main():
    """Main entry point"""
    logger.info("Starting geographic data collection...")

    # Download VMRC data
    download_vmrc_data()

    # Process state registrations
    reg_data = process_state_registrations()
    if reg_data:
        logger.info(f"Processed registrations for {len(reg_data)} cities")

    # Generate EV estimates
    ev_data = generate_ev_estimates()
    if ev_data:
        logger.info(f"Generated EV estimates for {len(ev_data)} cities")

    logger.info("Geographic data collection complete!")

    # Print summary
    print("\n" + "=" * 60)
    print("GEOGRAPHIC DATA SUMMARY")
    print("=" * 60)

    if reg_data:
        print("\nVehicle Registrations (Top 5):")
        for c in reg_data[:5]:
            print(f"  {c['city']:<20} {c['total_vehicles']:>12,} ({c['market_share_pct']}%)")

    if ev_data:
        print("\nEstimated EV/Hybrid Sales 2023 (Top 5):")
        for c in ev_data[:5]:
            print(f"  {c['city']:<20} {c['estimated_ev_sales_2023']:>12,} ({c['ev_hybrid_share_pct']}%)")


if __name__ == "__main__":
    main()
