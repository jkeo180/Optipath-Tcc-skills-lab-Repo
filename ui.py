import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    return pd.read_csv('PLACES__Local_Data_for_Better_Health,_ZCTA_Data,_2025_release_20260330.csv')

@st.cache_data
def get_health_data(location: str):
    df = load_data()
    print(f"Location type: {type(location)}, value: {location}")
    df_filtered = df[df['LocationName'].astype(str).str.contains(str(location), case=False, na=False)]


    if df_filtered.empty:
        return f"No data found for '{location}'. Try a zip code like '77002'.", None, None

    summary = (
        df_filtered.groupby('Short_Question_Text')['Data_Value']
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )

    result = f"**Top health indicators for {location}:**\n\n"
    for indicator, value in summary.head(10).items():
        result += f"- {indicator}: {value:.1f}%\n"

    lat, lon = 29.7604, -95.3698 # fix this
    sample = df_filtered['Geolocation'].dropna()
    if not sample.empty:
        try:
            coords = sample.iloc[0].replace("POINT (", "").replace(")", "").split()
            lon, lat = float(coords[0]), float(coords[1])
        except Exception:
            pass

    return result, lat, lon

st.title("Health Data Dashboard")

# --- MULTIPLE ZIP FEATURE ---

zip_input = st.text_input("Enter ZIP code(s) (comma-separated):", "77002, 77030")
zip_codes = [z.strip() for z in zip_input.split(",") if z.strip()]
for zip_code in zip_codes:
    st.subheader(f"Health Data for ZIP: {zip_code}")
    health_info, lat, lon = get_health_data()
    st.markdown(health_info)

    if lat and lon:
        m = folium.Map(location=[float(lat), float(lon)], zoom_start=12)
        folium.Marker([float(lat), float(lon)], tooltip=f"ZIP: {zip_code}").add_to(m)
        st_folium(m, width=700, height=500, key=f"map_{zip_code}")
    else:
        st.warning(f"No data found for ZIP code: {zip_code}")
