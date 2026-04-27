import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

@st.cache_data
def load_data():
    # EXACT filename from your repository
    filename = 'PLACES__Local_Data_for_Better_Health,_ZCTA_Data,_2025_release_20260330.csv'
    
    if not os.path.exists(filename):
        st.error(f"File Not Found: {filename}")
        st.info(f"Available files in repo: {os.listdir('.')}")
        return pd.DataFrame() # Return empty instead of None

    try:
        return pd.read_csv(filename)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return pd.DataFrame()

@st.cache_data
def get_health_data(location: str):
    df = load_data()
    
    if df.empty:
        return "Data currently unavailable.", None, None

    # Use LocationName for ZIP codes in the PLACES dataset
    df_filtered = df[df['LocationName'].astype(str).str.contains(str(location), case=False, na=False)]

    if df_filtered.empty:
        return f"No data found for '{location}'.", None, None

    summary = (
        df_filtered.groupby('Short_Question_Text')['Data_Value']
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )

    result = f"**Health indicators for {location}:**\n\n"
    for indicator, value in summary.head(10).items():
        result += f"- {indicator}: {value:.1f}%\n"

    # Default to Houston if no coords found
    lat, lon = 29.7604, -95.3698 
    
    if 'Geolocation' in df_filtered.columns:
        sample = df_filtered['Geolocation'].dropna()
        if not sample.empty:
            try:
                # Format: POINT (-95.3698 29.7604)
                coords = sample.iloc[0].replace("POINT (", "").replace(")", "").split()
                lon, lat = float(coords[0]), float(coords[1])
            except:
                pass

    return result, lat, lon

# --- UI LOGIC ---
st.title("Health Data Dashboard")
zip_input = st.text_input("Enter ZIP code(s) (comma-separated):", "77002, 77030")
zip_codes = [z.strip() for z in zip_input.split(",") if z.strip()]

for zip_code in zip_codes:
    st.divider()
    health_info, lat, lon = get_health_data(zip_code)
    st.markdown(health_info)

    if lat and lon:
        m = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], tooltip=f"ZIP: {zip_code}").add_to(m)
        st_folium(m, width=700, height=400, key=f"map_{zip_code}")


