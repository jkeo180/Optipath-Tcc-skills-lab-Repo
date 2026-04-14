import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    return pd.read_csv('C:\\Users\\11\\optipath data set1\\PLACES__Local_Data_for_Better_Health,_ZCTA_Data,_2025_release_20260330.csv')

@st.cache_data
def get_health_data(location: str):
    df = load_data()
    df_filtered = df[df['LocationName'].astype(str).str.contains(location, case=False, na=False)]

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

    lat, lon = 29.7604, -95.3698
    sample = df_filtered['Geolocation'].dropna()
    if not sample.empty:
        try:
            coords = sample.iloc[0].replace("POINT (", "").replace(")", "").split()
            lon, lat = float(coords[0]), float(coords[1])
        except Exception:
            pass

    return result, lat, lon

st.title("Health Data Dashboard")
search_query = st.text_input("Enter a zip code or location:", placeholder="e.g., 77002")

if search_query:
    result_text, lat, lon = get_health_data(search_query)
    st.write(f"DEBUG lat: {lat}, lon: {lon}")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Indicators")
        st.markdown(result_text)

    with col2:
        st.subheader("Location Map")
        m = folium.Map(location=[lat or 29.7604, lon or -95.3698], zoom_start=12)
        st_folium(m, width=350, height=400)
else:
    st.info("Enter a zip code above to see health indicators and a location map.")