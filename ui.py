import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. SETUP PAGE
st.set_page_config(page_title="Health Data Dashboard", layout="wide")
st.title("Health Data Dashboard")

# 2. DATA LOADING (Streaming directly from CDC to avoid GitHub file limits)
@st.cache_data
def load_data():
    # This is the actual direct download link for the 2025 ZCTA dataset
    url = "https://cdc.gov"
    
    try:
        # We ONLY pull the columns we need. This prevents "Out of Memory" crashes.
        cols = ['LocationName', 'Short_Question_Text', 'Data_Value', 'Geolocation']
        df = pd.read_csv(url, usecols=cols)
        
        # Clean up column names and types immediately
        df['LocationName'] = df['LocationName'].astype(str)
        return df
    except Exception as e:
        st.error(f"Error fetching data from CDC: {e}")
        return pd.DataFrame()

# 3. PROCESSING LOGIC
def get_health_data(df, zip_code):
    # Filter the main dataframe for the specific ZIP
    df_filtered = df[df['LocationName'] == str(zip_code)]

    if df_filtered.empty:
        return None, None, None

    # Calculate average values for indicators
    summary = (
        df_filtered.groupby('Short_Question_Text')['Data_Value']
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )

    # Format the text output
    text_results = f"### Top Indicators for {zip_code}\n"
    for indicator, value in summary.head(8).items():
        text_results += f"- **{indicator}**: {value:.1f}%\n"

    # Extract coordinates from Geolocation string: "POINT (-95.3 29.7)"
    lat, lon = 29.7604, -95.3698 # Default (Houston)
    if 'Geolocation' in df_filtered.columns:
        coords_raw = df_filtered['Geolocation'].dropna()
        if not coords_raw.empty:
            try:
                # Splitting the string to get numbers
                clean_coords = coords_raw.iloc[0].replace("POINT (", "").replace(")", "").split()
                lon, lat = float(clean_coords[0]), float(clean_coords[1])
            except:
                pass

    return text_results, lat, lon

# --- MAIN APP UI ---

# Load the data once at the start
with st.spinner("Downloading CDC Health Data (this may take a minute)..."):
    main_df = load_data()

if not main_df.empty:
    # User Input
    zip_input = st.text_input("Enter ZIP code(s) separated by commas:", "77002, 77030")
    user_zips = [z.strip() for z in zip_input.split(",") if z.strip()]

    # Create columns for multiple ZIPs
    cols = st.columns(len(user_zips)) if user_zips else []

    for i, zip_code in enumerate(user_zips):
        with st.container():
            st.divider()
            health_info, lat, lon = get_health_data(main_df, zip_code)
            
            if health_info:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(health_info)
                with col2:
                    # Create and display the map
                    m = folium.Map(location=[lat, lon], zoom_start=12)
                    folium.Marker([lat, lon], popup=f"ZIP: {zip_code}").add_to(m)
                    st_folium(m, width=600, height=350, key=f"map_{zip_code}")
            else:
                st.warning(f"No data found for ZIP: {zip_code}")
else:
    st.error("Data could not be loaded. Please check your internet connection.")
