import glob
import os
import pandas as pd
import pydeck as pdk
import streamlit as st

# 1. Page & App Configuration
st.set_page_config(
    page_title="Bus-Mounted AI Urban Sensing Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FOLDER = "../../ranked"

# 2. Clean UI Styling
st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #e0e6ed; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 13px; font-weight: 600; text-transform: uppercase; color: #94a3b8; margin-top: 6px;
    }
    .header-container { padding: 10px 0px 20px 0px; border-bottom: 1px solid #1e293b; margin-bottom: 25px; }
    .main-title { font-size: 32px; font-weight: 800; color: #f8fafc; }
    .subtitle { font-size: 15px; color: #64748b; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #21262d; }
    </style>
""",
    unsafe_allow_html=True,
)


def get_color(severity):
    sev = str(severity).lower()
    if sev == "high":
        return [239, 68, 68, 240]
    elif sev == "medium":
        return [245, 158, 11, 240]
    elif sev == "low":
        return [16, 185, 129, 240]
    return [56, 189, 248, 240]


# 3. Direct Folder Ingestion
def load_data_from_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return pd.DataFrame()

    files = glob.glob(os.path.join(folder_path, "*.json")) + glob.glob(
        os.path.join(folder_path, "*.csv")
    )

    if not files:
        return pd.DataFrame()

    all_data = []
    for filepath in files:
        try:
            if filepath.endswith(".json"):
                temp_df = pd.read_json(filepath)
                if "gps" in temp_df.columns:
                    gps_df = pd.json_normalize(temp_df["gps"])
                    temp_df["latitude"] = gps_df["lat"]
                    temp_df["longitude"] = gps_df["lng"]
            else:
                temp_df = pd.read_csv(filepath)

            all_data.append(temp_df)
        except Exception:
            pass

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined.drop_duplicates(subset=["event_id"], keep="last")
    return pd.DataFrame()


df = load_data_from_folder(DATA_FOLDER)

# Empty State View
if df.empty:
    st.markdown(
        """
        <div class="header-container">
            <div class="main-title">🤖 Bus-Mounted AI Urban Sensing</div>
            <div class="subtitle">Real-time edge event ingestion & spatial intelligence dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("⏳ **Awaiting Data:** Place event JSON or CSV files into `./data_outputs/`.")
    st.stop()

# Coordinate Normalization
if "gps.lat" in df.columns and "latitude" not in df.columns:
    df["latitude"] = df["gps.lat"]
if "gps.lng" in df.columns and "longitude" not in df.columns:
    df["longitude"] = df["gps.lng"]

# 4. Sidebar Event Filters Only
st.sidebar.title("🎛️ Control Panel")
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Event Filters")

category_col = (
    "event_type"
    if "event_type" in df.columns
    else ("category" if "category" in df.columns else None)
)

if category_col:
    categories = st.sidebar.multiselect(
        "Event Categories",
        options=sorted(df[category_col].dropna().unique()),
        default=df[category_col].dropna().unique(),
    )
    df = df[df[category_col].isin(categories)]

if "severity" in df.columns:
    severities = st.sidebar.multiselect(
        "Severity Tier",
        options=sorted(df["severity"].dropna().unique()),
        default=df["severity"].dropna().unique(),
    )
    df = df[df["severity"].isin(severities)]

if df.empty:
    st.warning("No events available for the selected filters.")
    st.stop()

if "severity" in df.columns:
    df["color"] = df["severity"].apply(get_color)
else:
    df["color"] = [[56, 189, 248, 240]] * len(df)

# Header & Overview KPIs
st.markdown(
    """
    <div class="header-container">
        <div class="main-title">🤖 Bus-Mounted AI Urban Sensing</div>
        <div class="subtitle">Autonomous road defect & traffic event monitoring platform</div>
    </div>
    """,
    unsafe_allow_html=True,
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df)}</div><div class="metric-label">Total Detections</div></div>', unsafe_allow_html=True)

with kpi2:
    cat_count = df[category_col].nunique() if category_col else "N/A"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{cat_count}</div><div class="metric-label">Event Classes</div></div>', unsafe_allow_html=True)

with kpi3:
    high_sev = len(df[df["severity"].astype(str).str.lower() == "high"]) if "severity" in df.columns else "N/A"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{high_sev}</div><div class="metric-label">Critical Alerts</div></div>', unsafe_allow_html=True)

with kpi4:
    lat_center = round(df["latitude"].mean(), 4)
    lon_center = round(df["longitude"].mean(), 4)
    st.markdown(f'<div class="metric-card"><div class="metric-value">{lat_center}, {lon_center}</div><div class="metric-label">Grid Center</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Map Configuration
avg_lat = df["latitude"].mean()
avg_lon = df["longitude"].mean()
view_state = pdk.ViewState(
    latitude=avg_lat,
    longitude=avg_lon,
    zoom=13,
    pitch=0
)

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["longitude", "latitude"],
    get_color="color",
    get_radius=100,
    radius_min_pixels=10,
    radius_max_pixels=30,
    pickable=True,
    stroked=True,
    get_line_color=[255, 255, 255, 255],
    line_width_min_pixels=2,
)

heatmap_layer = pdk.Layer(
    "HeatmapLayer",
    data=df,
    get_position=["longitude", "latitude"],
    get_weight=1,
    radiusPixels=50,
)

CARTO_DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

tab_map, tab_data = st.tabs(["🌍 Spatial Mapping", "📋 Raw Event Register"])

with tab_map:
    col_map1, col_map2 = st.columns(2)

    with col_map1:
        st.subheader("📍 Geolocation Point Map")
        st.pydeck_chart(
            pdk.Deck(
                map_style=CARTO_DARK_STYLE,
                layers=[scatter_layer],
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>ID:</b> {event_id}<br/><b>Type:</b> {event_type}<br/><b>Severity:</b> {severity}",
                    "style": {
                        "backgroundColor": "#1e293b",
                        "color": "#f8fafc",
                        "fontSize": "12px",
                        "borderRadius": "6px",
                        "padding": "8px",
                    },
                },
            )
        )

    with col_map2:
        st.subheader("🔥 Incident Density Heatmap")
        st.pydeck_chart(
            pdk.Deck(
                map_style=CARTO_DARK_STYLE,
                layers=[heatmap_layer],
                initial_view_state=view_state,
            )
        )

with tab_data:
    st.subheader("📊 Ingested Event Records")
    st.dataframe(
        df.drop(columns=["color"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
    )