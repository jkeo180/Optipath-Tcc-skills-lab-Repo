import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

@st.cache_data
def get_health_data(location: str):
    # Use the HF API to fetch rows for this specific ZIP
    # We use a large 'length' to ensure we get all indicators for that ZIP
    url = "https://huggingface.co"
    params = {
        "dataset": "HHS-Official/places-local-data-for-better-health-zcta-data-2023",
        "config": "default",
        "split": "train",
        "offset": 0, 
        "length": 100 
    }
    
    try:
        response = requests.get(url, params=params)
        # Note: In a real 'huge' dataset, you'd ideally use a search API, 
        # but for now, we'll mimic your filter logic on the returned chunk.
        data = response.json()
        rows = [r['row'] for r in data['rows']]
        df = pd.DataFrame(rows)
        
        # Filter based on your ZIP input
        df_filtered = df[df['LocationName'].astype(str).str.contains(str(location), case=False, na=False)]
    except Exception as e:
        return f"Error connecting to dataset: {e}", None, None

    if df_filtered.empty:
        return f"No data found for '{location}' in this batch.", None, None

    # Your existing summary logic
    summary = (
        df_filtered.groupby('Short_Question_Text')['Data_Value']
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )

    result = f"**Top health indicators for {location}:**\n\n"
    for indicator, value in summary.head(10).items():
        result += f"- {indicator}: {value:.1f}%\n"

    # Your existing Geolocation logic
    lat, lon = 29.7604, -95.3698 
    if 'Geolocation' in df_filtered.columns:
        sample = df_filtered['Geolocation'].dropna()
        if not sample.empty:
            try:
                # API format might be a dict or string; adjusting for common HF formats
                geo = sample.iloc[0]
                if isinstance(geo, dict) and 'coordinates' in geo:
                    lon, lat = geo['coordinates']
                else:
                    coords = str(geo).replace("POINT (", "").replace(")", "").split()
                    lon, lat = float(coords[0]), float(coords[1])
            except: pass

    return result, lat, lon

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
