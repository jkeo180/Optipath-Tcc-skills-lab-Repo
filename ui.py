import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import io


@st.cache_data
def get_health_data(zip_code: str):
    url = f"https://data.cdc.gov/resource/cwsq-ngmh.json?locationname={zip_code}&$limit=500"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"Error: Could not reach CDC (Status {response.status_code})", None, None

        df = pd.DataFrame(response.json())

        if df.empty:
            return f"No records found for ZIP {zip_code}.", None, None

        df['data_value'] = pd.to_numeric(df['data_value'], errors='coerce')

        summary = (
            df.groupby('measure')['data_value']
            .mean()
            .dropna()
            .sort_values(ascending=False)
            .head(10)
        )

        result = f"**Health Indicators for ZIP {zip_code}:**\n\n"
        for indicator, value in summary.items():
            result += f"- {indicator}: {value:.1f}%\n"

        lat, lon = 29.7604, -95.3698
        if 'geolocation' in df.columns:
            sample = df['geolocation'].dropna()
            if not sample.empty:
                try:
                    geo = sample.iloc[0]
                    if isinstance(geo, dict) and 'coordinates' in geo:
                        lon, lat = geo['coordinates']
                    else:
                        coords = str(geo).replace("POINT (", "").replace(")", "").split()
                        lon, lat = float(coords[0]), float(coords[1])
                except:
                    pass

        return result, lat, lon

    except Exception as e:
        return f"Error fetching data: {e}", None, None

st.title("Health Data Dashboard")
zip_input = st.text_input("Enter ZIP code(s) (comma-separated):", "77002, 77030")
zip_codes = [z.strip() for z in zip_input.split(",") if z.strip()]

for zip_code in zip_codes:
    st.subheader(f"Health Data for ZIP: {zip_code}")
    health_info, lat, lon = get_health_data(zip_code)
    st.markdown(health_info)
    if lat and lon:
        m = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], popup=f"ZIP: {zip_code}").add_to(m)
        st_folium(m, width=700, height=400, key=f"map_{zip_code}")
    else:
        st.warning(f"No map data for ZIP: {zip_code}")
