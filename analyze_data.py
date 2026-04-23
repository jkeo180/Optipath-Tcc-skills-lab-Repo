import pandas as pd
import os

# LOAD CSV FILES
df_cdc = pd.read_csv("PLACES__Local_Data_for_Better_Health,_Census_Tract_Data,_2025_release_20260324.csv")
df_usda = pd.read_csv("Food Access Research Atlas.csv")
df_clean = pd.read_csv("clean_map_data.csv")

# KEYS
df_cdc['LocationID'] = df_cdc['LocationID'].astype(str).str.strip()
df_usda['CensusTract'] = df_usda['CensusTract'].astype(str).str.strip()
df_clean['Geolocation'] = df_clean['Geolocation'].astype(str).str.strip()
# Merge Data
df_merged = pd.merge(
    df_cdc, 
    df_usda,
    left_on='LocationID', 
    right_on='CensusTract', 
    how='left'
)

# Merge the result with clean_map_data (Coordinates)
df = pd.merge(
    df_merged,
    df_clean,
    left_on='LocationID',
    right_on='Geolocation',
    how='left'
)
# 4. CLEAN & RENAME (Fixed for Merged Suffixes)
column_map = {
    'Data_Value_x': 'Data Value',      
    'LocationName': 'Location',
    'Measure': 'Short Indicator Text',
    'Short_Question_Text_x': 'Short Question Text', # The x version from CDC
    'Measure_Identifier': 'Short Indicator Text'
}

# Apply the rename
df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})

# Fallback: if Data_Value_x wasn't found, try the standard Data_Value
if 'Data Value' not in df.columns and 'Data_Value' in df.columns:
    df = df.rename(columns={'Data_Value': 'Data Value'})

# Final Check
if 'Data Value' not in df.columns:
    print("CRITICAL ERROR: Could not find the data value column.")
    print(f"Current columns: {df.columns.tolist()}")
    exit()

# Ensure numeric data
df['Data Value'] = pd.to_numeric(df['Data Value'], errors='coerce')

# FILTER (TX Diabetes & Harris County)
df_filtered = df[
    (df['StateAbbr'].str.strip().str.upper() == "TX") & 
    (df['Short Question Text'].str.contains("Diabetes", case=False, na=False)) &
    (df['CountyName'].str.contains("Harris", case=False, na=False))
].dropna(subset=['Data Value'])

# RESULTS
print(f"Success! Total Houston/Harris County records: {len(df_filtered)}")
# Use the LILA column for stats (Low Income, Low Access)
lila_col = [c for c in df_filtered.columns if 'LILA' in c]
if lila_col:
    print(f"\nFound Food Desert column: {lila_col[0]}")
    # This shows average diabetes rate in Food Deserts vs Non-Food Deserts
    print(df_filtered.groupby(lila_col[0])['Data Value'].mean())
