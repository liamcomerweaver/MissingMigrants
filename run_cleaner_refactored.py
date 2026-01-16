#!/usr/bin/env python
# coding: utf-8
"""
Missing Migrants Dataset Cleaner - Refactored Version
Runs the cleaning process from MM_Cleaner_Refactored_28.ipynb
"""

# Core packages
import pandas as pd
import numpy as np
import sys

print("=" * 80)
print("Missing Migrants Dataset Cleaner - Refactored Version")
print("=" * 80)

# ============================================================================
# B: Import Dataset
# ============================================================================
print("\n[1/13] Importing dataset from IOM...")
MM = pd.read_csv(
    'https://missingmigrants.iom.int/sites/g/files/tmzbdl601/files/report-migrant-incident/Missing_Migrants_Global_Figures_allData.csv?420491',
    index_col=False,
    encoding='unicode_escape'
)
print(f"✓ Loaded {len(MM):,} records")

# ============================================================================
# C: Rename Columns
# ============================================================================
print("\n[2/13] Renaming columns...")
MM = MM.drop(MM.columns[0], axis=1)  # Drop first column (Main ID with BOM)

columns = [
    "Incident_ID", "Incident_Type", "Region", "Reported_Date", "Reported_Year",
    "Reported_Month", "Number_Dead", "Minimum_Missing", "Total_Dead_and_Missing",
    "Survivors", "Females", "Males", "Children", "Country_of_Origin",
    "Region_of_Origin", "Cause_of_Death", "Country_of_Incident", "Migration_Route",
    "Location_Description", "Coordinates", "UNSD_Geographical_Grouping",
    "Information_Source", "URL", "Source_Quality"
]
MM.columns = columns
print(f"✓ Renamed to {len(columns)} columns")

# ============================================================================
# D: Clean Country of Origin
# ============================================================================
print("\n[3/13] Cleaning Country of Origin...")
MM['Country_of_Origin'] = MM['Country_of_Origin'].fillna('Unknown').astype(str)

infrequent_countries = {
    'nan', 'Viet Nam', 'Liberia', 'Burundi', 'Lesotho', 'Mauritania', 'Malawi',
    'Uzbekistan', 'Nepal', 'Madagascar', 'Mozambique', 'Lebanon', 'Costa Rica',
    'Malaysia', 'Kenya', 'Central African Republic', 'Kyrgyzstan', 'Jamaica',
    'Uruguay', 'Israel', 'Eswatini', 'Paraguay', 'Albania', 'Guyana',
    'Republic of Korea', "Lao People's Democratic Republic", 'Oman', 'South Sudan',
    'Burkina Faso', 'Bahamas', 'Papua New Guinea', 'Belize', 'Georgia', 'Togo',
    'Russian Federation'
}

conditions = [
    MM['Country_of_Origin'].str.contains('Unknown', case=False, na=False),
    MM['Country_of_Origin'].str.contains(',', na=False),
    MM['Country_of_Origin'].str.contains('Mixed|multiple', case=False, na=False),
    MM['Country_of_Origin'].isin(infrequent_countries)
]
choices = ['Unknown', 'Multiple Countries', 'Multiple Countries', 'Infrequent Countries']
MM['Country_of_Origin'] = np.select(conditions, choices, default=MM['Country_of_Origin'])
print(f"✓ Bucketed into {MM['Country_of_Origin'].nunique()} categories")

# ============================================================================
# E: Clean Cause of Death
# ============================================================================
print("\n[4/13] Cleaning Cause of Death...")
MM['Cause_of_Death'] = MM['Cause_of_Death'].fillna('Unknown').astype(str)

conditions = [
    MM['Cause_of_Death'].str.contains('lack of adequate shelter|harsh environmental', case=False, na=False),
    MM['Cause_of_Death'].str.contains('drowning', case=False, na=False),
    MM['Cause_of_Death'].str.contains('mixed or unknown', case=False, na=False),
]
choices = ['Lack of Shelter, Food, or Water', 'Drowning', 'Mixed or unknown']
MM['Cause_of_Death'] = np.select(conditions, choices, default=MM['Cause_of_Death'])
print(f"✓ Standardized to {MM['Cause_of_Death'].nunique()} categories")

# ============================================================================
# F: Handle Missing Values
# ============================================================================
print("\n[5/13] Handling missing values...")
MM['Migration_Route'] = MM['Migration_Route'].fillna('Not Specified')
MM['Region'] = MM['Region'].fillna('Not Specified')

numeric_cols = ['Number_Dead', 'Minimum_Missing', 'Total_Dead_and_Missing',
                'Survivors', 'Females', 'Males', 'Children']
MM[numeric_cols] = MM[numeric_cols].fillna(0)
print(f"✓ Filled missing values in {len(numeric_cols)} numeric columns")

# ============================================================================
# G: One-Hot Encode Cause of Death
# ============================================================================
print("\n[6/13] Creating one-hot encoded Cause of Death columns...")
MM = pd.get_dummies(MM, columns=['Cause_of_Death'], prefix='COD', prefix_sep='_')
cod_cols = [c for c in MM.columns if c.startswith('COD_')]
print(f"✓ Created {len(cod_cols)} dummy columns")

# ============================================================================
# H: Parse Coordinates
# ============================================================================
print("\n[7/13] Parsing coordinates into Latitude/Longitude...")
coords = (
    MM['Coordinates']
    .fillna('0, 0')
    .astype(str)
    .str.strip(',')
    .str.split(r'[,\s]+', expand=True, regex=True)
)
MM['Latitude'] = pd.to_numeric(coords[0], errors='coerce').fillna(0)
MM['Longitude'] = pd.to_numeric(coords[1], errors='coerce').fillna(0)
print(f"✓ Parsed {(MM['Latitude'] != 0).sum():,} valid coordinates")

# ============================================================================
# I: Create Log-Transformed Death Count
# ============================================================================
print("\n[8/13] Creating log-transformed death count for visualization...")
MM['Total_Dead_and_Missing'] = pd.to_numeric(
    MM['Total_Dead_and_Missing'].astype(str).str.replace(',', ''),
    errors='coerce'
).fillna(0)
MM['Log_Dead'] = MM['Total_Dead_and_Missing'] ** (1/3) * 3
print(f"✓ Log_Dead range: {MM['Log_Dead'].min():.2f} to {MM['Log_Dead'].max():.2f}")

# ============================================================================
# J: Clean URLs
# ============================================================================
print("\n[9/13] Extracting first URL from URL field...")
MM['URL'] = MM['URL'].fillna('Not Given')
MM['URL1'] = MM['URL'].str.split(',').str[0]
print(f"✓ Extracted primary URLs")

# ============================================================================
# K: Create Derived Sex/Age Variables
# ============================================================================
print("\n[10/13] Creating derived sex/age variables...")
count_cols = ['Total_Dead_and_Missing', 'Females', 'Males', 'Children']
for col in count_cols:
    MM[col] = pd.to_numeric(MM[col], errors='coerce').fillna(0)

MM['Unknown_Sex'] = MM['Total_Dead_and_Missing'] - MM['Females'] - MM['Males']
MM['Unknown_Age_Status'] = MM['Total_Dead_and_Missing'] - MM['Children']
MM['Confirmed_Adults'] = np.where(
    MM['Unknown_Age_Status'] != 0,
    MM['Males'] + MM['Females'] - MM['Children'],
    0
)
print(f"✓ Created Unknown_Sex, Unknown_Age_Status, Confirmed_Adults")

# ============================================================================
# L: Reverse Geocode Coordinates
# ============================================================================
print("\n[11/13] Reverse geocoding coordinates to countries...")
try:
    import reverse_geocoder as rg

    valid_mask = (MM['Latitude'] != 0) & (MM['Longitude'] != 0)
    coords = list(zip(
        MM.loc[valid_mask, 'Latitude'],
        MM.loc[valid_mask, 'Longitude']
    ))

    print(f"  Geocoding {len(coords):,} coordinates...")
    results = rg.search(coords)

    MM['Country'] = 'International Waters'
    MM.loc[valid_mask, 'Country'] = [r['cc'] for r in results]
    MM.loc[valid_mask, 'Country_Name'] = [r['name'] for r in results]

    print(f"✓ Geocoded successfully")

except ImportError:
    print("  ⚠ reverse_geocoder not installed, using Country_of_Incident as fallback")
    MM['Country'] = MM['Country_of_Incident'].fillna('Unknown')

# ============================================================================
# M: Create Date Column
# ============================================================================
print("\n[12/13] Creating standardized Date column...")
month_map = {
    'January': '01', 'February': '02', 'March': '03', 'April': '04',
    'May': '05', 'June': '06', 'July': '07', 'August': '08',
    'September': '09', 'October': '10', 'November': '11', 'December': '12'
}
MM['Date'] = pd.to_datetime(
    MM['Reported_Year'].astype(str) + '-' +
    MM['Reported_Month'].map(month_map) + '-01',
    errors='coerce'
)
print(f"✓ Date range: {MM['Date'].min()} to {MM['Date'].max()}")

# ============================================================================
# N: Final Column Cleanup
# ============================================================================
print("\n[13/13] Final column cleanup...")
rename_map = {
    'Country_of_Origin': 'Country of Origin',
    'Region_of_Origin': 'Region of Origin',
    'Country_of_Incident': 'Country of Incident',
    'Migration_Route': 'Migration Route',
    'Location_Description': 'Location Description',
    'Information_Source': 'Info Source',
    'UNSD_Geographical_Grouping': 'UNSD_Geographical_Grouping'
}
MM = MM.rename(columns=rename_map)
print(f"✓ Renamed columns for consistency")

# ============================================================================
# O: Export to CSV
# ============================================================================
print("\n" + "=" * 80)
print("EXPORTING CLEANED DATASET")
print("=" * 80)

output_path = 'MM_Dummies_CleanRefactored_Jan16.csv'
MM.to_csv(output_path, index=False)

print(f"\n✓ Saved to: {output_path}")
print(f"\n=== Dataset Summary ===")
print(f"Records: {len(MM):,}")
print(f"Columns: {len(MM.columns)}")
print(f"Date range: {MM['Date'].min().date()} to {MM['Date'].max().date()}")
print(f"Total dead/missing: {MM['Total_Dead_and_Missing'].sum():,.0f}")
print(f"Unique countries of incident: {MM['Country of Incident'].nunique()}")
print(f"Unique migration routes: {MM['Migration Route'].nunique()}")
print("\n" + "=" * 80)
print("CLEANING COMPLETE!")
print("=" * 80)
