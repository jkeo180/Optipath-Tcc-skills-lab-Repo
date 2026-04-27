import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    try:
       def load_data():
           return pd.read_csv('PLACES__Local_Data_for_Better_Health,_ZCTA_Data,_2025_release_20260330.csv')
    except Exception as e:
        # If the file is missing or broken, return an empty box (DataFrame)
        # instead of letting the app crash with 'NoneType'
        st.error(f"Could not load CSV: {e}")
        return pd.DataFrame() 

@st.cache_data
def get_health_data(location: str):
    df = load_data()
    
    # Safety check: if df is empty, stop here
    if df.empty:
        return "Database is empty or file not found.", None, None

    # Filter data
    df_filtered = df[df['LocationName'].astype(str).str.contains(str(location), case=False, na=False)]

    if df_filtered.empty:
        return f"No data found for '{location}'. Try a zip code like '77002'.", None, None

    # Calculate summary
    summary = (
        df_filtered.groupby('Short_Question_Text')['Data_Value']
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )

    result = f"**Top health indicators for {location}:**\n\n"
    for indicator, value in summary.head(10).items():
        result += f"- {indicator}: {value:.1f}%\n"

    # Default coordinates (Houston)
    lat, lon = 29.7604, -95.3698 
    
    # Parse Geolocation
    if 'Geolocation' in df_filtered.columns:
        sample = df_filtered['Geolocation'].dropna()
        if not sample.empty:
            try:
                # Cleaning "POINT (-95.3698 29.7604)"
                raw_coords = sample.iloc[0].replace("POINT (", "").replace(")", "").split()
                lon, lat = float(raw_coords[0]), float(raw_coords[1])
            except Exception:
                pass

    return result, lat, lon

# --- UI LOGIC ---

st.title("Health Data Dashboard")

zip_input = st.text_input("Enter ZIP code(s) (comma-separated):", "77002, 77030")
zip_codes = [z.strip() for z in zip_input.split(",") if z.strip()]

for zip_code in zip_codes:
    st.divider() # Adds a nice line between ZIPS
    st.subheader(f"Health Data for ZIP: {zip_code}")
    
    # This now receives exactly 3 things because of the 'return' at the end of the function
    health_info, lat, lon = get_health_data(zip_code)
    st.markdown(health_info)

    if lat and lon:
        m = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], tooltip=f"ZIP: {zip_code}").add_to(m)
        # Use a unique key for each map so Streamlit doesn't get confused
        st_folium(m, width=700, height=400, key=f"map_{zip_code}")


