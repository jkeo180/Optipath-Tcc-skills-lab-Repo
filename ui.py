import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    return pd.read_csv('PLACES__Local_Data_for_Better_Health,_ZCTA_Data,_2025_release_20260330.csv')
df = load_data()

# 1. Define 'location' FIRST via user input
location = st.text_input("Enter ZIP code", value="77002")

# 2. Use 'location' to create 'df_filtered'
if location:
    # In the PLACES ZCTA dataset, ZIP codes are often in 'LocationName' or 'LocationID'
    # We cast to string to ensure the comparison works
    df_filtered = df[df['LocationName'].astype(str) == str(location)]

    if df_filtered.empty:
        st.warning(f"No data found for ZIP code: {location}")
        st.stop()
    
    # 3.summary logic
    summary = (
        df_filtered.groupby('Short_Question_Text')['Data_Value']
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )
    st.write(f"### Health Indicators for {location}")
    st.dataframe(summary)
    st.write(f"**Top health indicators for {location}:**")
    st.table(summary) # Or however you'd like to display it
else:
    st.info("Please enter a ZIP code to begin.")
    st.stop()
    result = f"**Top health indicators for {location}:**\n\n"
    for indicator, value in summary.head(10).items():
        result += f"- {indicator}: {value:.1f}%\n"

lat, lon = 29.7604, -95.3698 
sample = df_filtered['Geolocation'].dropna()

if not sample.empty:
    try:
       
        coords = sample.iloc[0].replace("POINT (", "").replace(")", "").split()
        lon, lat = float(coords[0]), float(coords[1])
    except Exception:
        pass

st.write(f"Showing results for coordinates: {lat}, {lon}")

st.title("Health Data Dashboard")

# --- MULTIPLE ZIP FEATURE ---

zip_input = st.text_input("Enter ZIP code(s) (comma-separated):", "77002, 77030")
zip_codes = [z.strip() for z in zip_input.split(",") if z.strip()]
for zip_code in zip_codes:
    st.subheader(f"Health Data for ZIP: {zip_code}")
    health_info, lat, lon = get_health_data(zip_code)
    st.markdown(health_info)

    if lat and lon:
        folium.Marker(
        [float(lat), float(lon)], 
        tooltip=f"ZIP: {zip_code}"
    ).add_to(m)
        st_folium(m, width=700, height=500, key=f"map_{zip_code}")
    else:
        st.warning(f"No data found for ZIP code: {zip_code}")
