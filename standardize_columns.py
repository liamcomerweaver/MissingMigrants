#!/usr/bin/env python3
"""
Standardize MM_Dummies_CleanRefactored_Jan16.csv to match old column naming convention
"""
import pandas as pd

print("=" * 80)
print("Standardizing Column Names to Match Old Convention")
print("=" * 80)

# Load the new file
print("\n[1/3] Loading MM_Dummies_CleanRefactored_Jan16.csv...")
df = pd.read_csv('MM_Dummies_CleanRefactored_Jan16.csv')
print(f"✓ Loaded {len(df):,} records with {len(df.columns)} columns")

# Define column renaming map
print("\n[2/3] Renaming columns to match old convention...")
rename_map = {
    # Remove COD_ prefix and standardize names
    'COD_Accidental death': 'Other Accidents',
    'COD_Drowning': 'Drowning',
    'COD_Lack of Shelter, Food, or Water': 'Lack of Shelter, Food, or Water',
    'COD_Mixed or unknown': 'Mixed or unknown',
    'COD_Sickness / lack of access to adequate healthcare': 'Sickness',
    'COD_Vehicle accident / death linked to hazardous transport': 'Transportation Accident',
    'COD_Violence': 'Violence',

    # Fix formatting differences
    'Migration Route': 'Migration_Route',
    'Source_Quality': 'Source Quality'
}

df = df.rename(columns=rename_map)
print(f"✓ Renamed {len(rename_map)} columns")

# Reorder columns to match old file convention
print("\n[3/3] Reordering columns to match old file structure...")
desired_order = [
    'Incident_ID', 'Incident_Type', 'Region', 'Reported_Date', 'Reported_Year',
    'Reported_Month', 'Number_Dead', 'Minimum_Missing', 'Total_Dead_and_Missing',
    'Survivors', 'Females', 'Males', 'Children', 'Country of Origin',
    'Region of Origin', 'Country of Incident', 'Migration_Route',
    'Location Description', 'Coordinates', 'UNSD_Geographical_Grouping',
    'Info Source', 'URL', 'Source Quality',
    'Other Accidents', 'Drowning', 'Lack of Shelter, Food, or Water',
    'Mixed or unknown', 'Sickness', 'Transportation Accident', 'Violence',
    'Latitude', 'Longitude', 'Log_Dead', 'URL1', 'Unknown_Sex',
    'Unknown_Age_Status', 'Country', 'Confirmed_Adults', 'Date'
]

# Reorder columns (keep any extra columns at the end)
existing_cols = [col for col in desired_order if col in df.columns]
extra_cols = [col for col in df.columns if col not in desired_order]
df = df[existing_cols + extra_cols]

print(f"✓ Reordered columns")

# Save the standardized file
output_path = 'MM_Dummies_CleanRefactored_Jan16.csv'
df.to_csv(output_path, index=False)

print("\n" + "=" * 80)
print("STANDARDIZATION COMPLETE")
print("=" * 80)
print(f"\n✓ Saved to: {output_path}")
print(f"\nFinal structure:")
print(f"  Records: {len(df):,}")
print(f"  Columns: {len(df.columns)}")
print(f"\nCause of Death columns (now WITHOUT COD_ prefix):")
cod_columns = ['Other Accidents', 'Drowning', 'Lack of Shelter, Food, or Water',
               'Mixed or unknown', 'Sickness', 'Transportation Accident', 'Violence']
for col in cod_columns:
    if col in df.columns:
        print(f"  ✓ {col}")
print("\n" + "=" * 80)
