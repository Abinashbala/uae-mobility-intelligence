import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# =========================================================
# 0. PLATFORM INITIALIZATION
# =========================================================
st.set_page_config(page_title="UAE Mobility Twin", page_icon="🚦", layout="wide")

# =========================================================
# 1. CONFIGURATION & METADATA LAYER
# =========================================================
CITY_COORDS = {
    'Dubai': {'lat': 25.2048, 'lon': 55.2708},
    'Abu Dhabi': {'lat': 24.4539, 'lon': 54.3773},
    'Ras Al Khaimah': {'lat': 25.7895, 'lon': 55.9432},
    'Al Ain': {'lat': 24.1302, 'lon': 55.8023},
    'Fujairah': {'lat': 25.1288, 'lon': 56.3265}
}

# =========================================================
# 2. PREMIUM CSS
# =========================================================
st.markdown("""
<style>
    .stApp { background-color: #0A0F1C !important; color: #F8FAFC !important; font-family: 'Inter', sans-serif !important; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #101826 0%, #0B111C 100%) !important; border-right: 1px solid #1E293B !important; }
    div[data-baseweb="select"] { background-color: #161F2E !important; border: 1px solid #263244 !important; border-radius: 8px !important; }
    div[data-baseweb="select"] * { background-color: #161F2E !important; color: white !important; }
    div[data-testid="metric-container"] { 
        background: linear-gradient(145deg, #131C2C, #101826) !important; 
        border: 1px solid #1F2A3D !important; padding: 14px 12px !important; border-radius: 12px !important; 
        min-width: 0; 
    }
    div[data-testid="metric-container"]:hover { border: 1px solid #3A86FF !important; transform: translateY(-2px) !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.65rem !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px !important; color: #94A3B8 !important;}
    div[data-testid="stMetricValue"] { font-size: 1.15rem !important; font-weight: 800 !important; line-height: 1.2 !important; white-space: normal !important; word-wrap: break-word !important; }
    div[data-testid="stMetricDelta"] { font-size: 0.70rem !important; margin-top: 6px !important; }
    .element-container:has(.js-plotly-plot) {
        background: linear-gradient(145deg, #111827, #0F172A) !important; padding: 16px !important; border-radius: 12px !important; border: 1px solid #1F2937 !important;
    }
    hr { border-color: #1E293B !important; margin: 2.5rem 0 !important; }
    .sim-warning { color: #FF8FA3; font-size: 0.75rem; margin-top: -5px; margin-bottom: 10px; opacity: 0.8; }
    
    .weather-context {
        background-color: rgba(0, 229, 255, 0.05);
        border-left: 3px solid #00E5FF;
        padding: 10px 12px;
        margin-top: 15px;
        border-radius: 0 4px 4px 0;
        font-size: 0.85rem;
        color: #E2E8F0;
    }
    .weather-context strong { color: #00E5FF; }
    .live-badge {
        background-color: #FF006E;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 800;
        margin-left: 6px;
        vertical-align: middle;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. DATA INGESTION (TRAFFIC & WEATHER)
# =========================================================
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("data/uae_traffic_intelligence_master.csv")
    except:
        data = pd.read_csv("../data/processed/uae_traffic_intelligence_master.csv")
    data['City_UI'] = data['City'].str.replace('-', ' ').str.title().replace({'Abu Dhabi': 'Abu Dhabi', 'Ras Al Khaimah': 'Ras Al Khaimah'})
    return data

df = load_data()

@st.cache_data(ttl=900)
def fetch_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&timezone=auto"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()['current']
        return None
    except:
        return None

# =========================================================
# 4. DIAGNOSTIC TYPOLOGY & WEATHER ENGINE
# =========================================================
def get_typology_diagnosis(f, d, j):
    if f > 10 and d > 2.0 and j > 450: return "Severe Congestion Pressure"
    if f > 7 and d > 1.5 and j > 250: return "Widespread Congestion"
    if f > 4 and d > 1.0 and j > 120: return "Heavy Traffic Conditions"
    if f > 2 and d > 0.5 and j > 40: return "Moderate Traffic Build-Up"
    return "Smooth Traffic Flow"

def get_weather_interpretation(w_code, temp, wind):
    # FIX 3 & 4: Softened, observational narratives
    if w_code in [0, 1, 2]:
        context = "Stable atmospheric conditions."
        state = "Clear"
    elif w_code in [3]:
        context = "Overcast conditions detected. Marginal impact on overall visibility."
        state = "Overcast"
    elif w_code in [45, 48]:
        context = "Fog detected. Reduced visibility conditions may affect driving conditions during peak commuter periods."
        state = "Fog/Low Visibility"
    elif w_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        context = "Precipitation detected. Wet road conditions may contribute to slower commuter movement across key corridors."
        state = "Rain/Showers"
    elif w_code in [71, 73, 75, 77, 85, 86, 95, 96, 99]:
        context = "Severe weather conditions detected. Potential for disrupted mobility and localized slowdowns."
        state = "Severe Weather"
    else:
        context = "Environmental conditions nominal."
        state = "Stable"
        
    if wind > 30:
        context += " High wind speeds may affect elevated highway corridors."
    
    return state, context

def get_speed_interpretation(raw_p, raw_d):
    if abs(raw_d) < 1.0: return "Near Baseline", "Nominal variance", "off"
    if abs(raw_p) < 1: return "Normal Flow", "Within baseline", "off"
    if raw_p > 0: return f"{abs(raw_p):.1f}% Slower", "Traffic slowdown", "inverse"
    return f"{abs(raw_p):.1f}% Faster", "Traffic flowing well", "normal"

def get_delay_interpretation(norm_d):
    if norm_d < 0.5: return "Minimal Delay", "Roads stable", "normal"
    if norm_d < 2: return f"{norm_d:.1f} Min Delay", "Moderate slowdown", "inverse"
    return f"{norm_d:.1f} Min Delay", "Heavy commuter impact", "inverse"

def get_queue_interpretation(norm_j):
    if norm_j < 40: return f"{norm_j:.1f} KM", "Light buildup", "normal"
    if norm_j < 120: return f"{norm_j:.1f} KM", "Moderate queue pressure", "inverse"
    return f"{norm_j:.1f} KM", "Widespread congestion buildup", "inverse" 

def get_risk_interpretation(risk_score):
    if risk_score < 5: return "Low", "Stable mobility", "normal"
    if risk_score < 15: return "Moderate", "Localized instability", "inverse"
    if risk_score < 30: return "High", "Escalation possible", "inverse"
    return "Severe", "Major congestion pressure", "inverse" 

# =========================================================
# 5. SIDEBAR CONTROLS
# =========================================================
st.sidebar.title("🚦 Operations Console")
selected_city = st.sidebar.selectbox("🌐 Target Sector", options=sorted(df['City_UI'].unique()))

selected_severity = st.sidebar.selectbox("🚨 Simulation Scenario", 
    options=["Observed Conditions", "Low", "Moderate", "High", "Severe"])

if selected_severity != "Observed Conditions":
    st.sidebar.markdown("<small style='color:#FF006E; font-weight:600;'>Simulation Mode Active</small>", unsafe_allow_html=True)

st.sidebar.markdown("### ⏱️ Time Window")
c1, c2 = st.sidebar.columns(2)
with c1: h_clock = st.selectbox("Hour", options=[12,1,2,3,4,5,6,7,8,9,10,11], format_func=lambda x: f"{x}:00", label_visibility="collapsed")
with c2: period = st.selectbox("Period", options=["AM", "PM"], label_visibility="collapsed")

target_h = h_clock + (12 if period == "PM" and h_clock != 12 else 0)
if period == "AM" and h_clock == 12: target_h = 0

m_style = "carto-positron" if period == "AM" else "carto-darkmatter"
m_cols = ['#00E5FF', '#7C3AED', '#FF006E'] 

# =========================================================
# 6. OPERATIONAL FILTERING + REALISTIC SCENARIO ENGINE
# =========================================================
f_df = df[(df['City_UI'] == selected_city) & (df['Hour'] == target_h)].copy()

if len(f_df) == 0:
    st.warning("No operational data available for selected conditions.")
    st.stop()

base_f = f_df['TrafficFrictionScore'].mean()
base_p = f_df['TravelTimeInflationPct'].mean()
base_j = f_df['JamLengthKm'].mean()
base_d = f_df['TravelDelayMinutes'].mean()
base_r = f_df['NetworkShockEscalation'].mean()

hour_baseline = df[(df['City_UI'] == selected_city) & (df['Hour'] == target_h)]['TrafficFrictionScore'].mean()
hour_factor = max(hour_baseline, 0.5)

scenario_multipliers = {
    "Observed Conditions": {"f": 1.0, "p": 1.0, "j": 1.0, "d": 1.0, "r": 1.0},
    "Low": {"f": 0.7, "p": 0.7, "j": 0.7, "d": 0.7, "r": 0.6},
    "Moderate": {"f": 1.0, "p": 1.0, "j": 1.0, "d": 1.0, "r": 1.0},
    "High": {"f": 1.35, "p": 1.45, "j": 1.5, "d": 1.4, "r": 1.5},
    "Severe": {"f": 1.8, "p": 2.0, "j": 2.2, "d": 2.0, "r": 2.0}
}
mult = scenario_multipliers[selected_severity]

raw_f = base_f * mult['f']; raw_p = base_p * mult['p']
raw_j = base_j * mult['j']; raw_d = base_d * mult['d']
raw_r = base_r * mult['r']

if target_h in [0, 1, 2, 3, 4]: raw_f *= 0.65; raw_j *= 0.6; raw_d *= 0.5; raw_r *= 0.55
if target_h in [5, 6]: raw_f *= 0.8; raw_j *= 0.8; raw_d *= 0.8
if target_h in [16, 17, 18, 19]: raw_f *= 1.2; raw_j *= 1.25; raw_d *= 1.3; raw_r *= 1.2

norm_f = max(raw_f, 0); norm_d = max(raw_d, 0); norm_j = max(raw_j, 0)
context_f = norm_f / hour_factor

f_state = get_typology_diagnosis(norm_f, norm_d, norm_j)
p_display, p_delta, p_color = get_speed_interpretation(raw_p, raw_d)
d_display, d_delta, d_color = get_delay_interpretation(norm_d)
j_display, j_delta, j_color = get_queue_interpretation(norm_j)

risk_score = min(max(raw_r, 0) * (((context_f * 0.8) + (norm_d * 1.2) + (norm_j / 180)) / 6), 100)
r_display, r_delta, r_color = get_risk_interpretation(risk_score)

if norm_j < 40: congestion_label = "Localized"
elif norm_j < 120: congestion_label = "Moderate"
elif norm_j < 250: congestion_label = "Widespread"
else: congestion_label = "Network-Wide"

w_data = fetch_live_weather(CITY_COORDS[selected_city]['lat'], CITY_COORDS[selected_city]['lon'])
weather_state, weather_context = "Nominal", "Live environmental telemetry unavailable."
if w_data:
    weather_state, weather_context = get_weather_interpretation(w_data['weather_code'], w_data['temperature_2m'], w_data['wind_speed_10m'])

# =========================================================
# 7. EXECUTIVE KPI VIEW
# =========================================================
st.title("🚦 UAE Mobility Intelligence")
st.markdown("## 📡 Localized Network Status")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Network State", f_state, f"Relative Load {context_f:.1f}x", delta_color="off")
k2.metric("Travel Speed", p_display, p_delta, delta_color=p_color)
k3.metric("Congestion Spread", congestion_label, f"~{norm_j:.0f} km affected roadway", delta_color=j_color)
k4.metric("Delay Impact", d_display, d_delta, delta_color=d_color)
k5.metric("Gridlock Risk", r_display, r_delta, delta_color=r_color)

# =========================================================
# 8. PREDICTIVE & DIAGNOSTIC INTELLIGENCE LAYER
# =========================================================
st.markdown("---")

col_diag, col_empty = st.columns([2, 1])
with col_diag:
    st.markdown("### 🧠 Operational Diagnosis")
    st.info(f"**Current Classification:** {f_state}")
    
    if f_state == "Severe Congestion Pressure":
        st.write("Peak congestion pressure detected across major commuter corridors. Travel movement remains active but significantly slowed during this operational window.")
    elif f_state == "Widespread Congestion":
        st.write("Congestion is spreading across multiple high-volume routes, increasing travel times throughout the network.")
    elif f_state == "Heavy Traffic Conditions":
        st.write("Sustained traffic pressure is slowing movement across key urban corridors.")
    elif f_state == "Moderate Traffic Build-Up":
        st.write("Traffic volume is gradually increasing, creating moderate congestion buildup.")
    else:
        st.write("Calm network operations. Movement is fluid and operating efficiently within expected historical parameters.")

    # FIX 1, 2 & 5: Live Environmental Conditions Badge & Rounded Temp
    if w_data:
        temp_rounded = round(w_data['temperature_2m'])
        st.markdown(f"""
        <div class='weather-context'>
            <strong>Current Environmental Conditions <span class='live-badge'>LIVE</span> ({weather_state} | {temp_rounded}°C):</strong> {weather_context}
        </div>
        """, unsafe_allow_html=True)


hours_to_plot = [(target_h - 2) % 24, (target_h - 1) % 24, target_h, (target_h + 1) % 24, (target_h + 2) % 24]
baseline_trajectory = []
sim_trajectory = []

for h in hours_to_plot:
    h_df = df[(df['City_UI'] == selected_city) & (df['Hour'] == h)]
    if len(h_df) > 0:
        b_f = max(h_df['TrafficFrictionScore'].mean(), 0)
        b_d = max(h_df['TravelDelayMinutes'].mean(), 0)
        b_j = max(h_df['JamLengthKm'].mean(), 0)
        
        b_sev = b_f + (b_d * 4) + (b_j / 120)
        baseline_trajectory.append({'Hour': f"{h:02d}:00", 'ForecastSeverity': b_sev, 'Trajectory': 'Observed Baseline'})
        
        if selected_severity != "Observed Conditions":
            if hours_to_plot.index(h) >= 2: 
                s_f = b_f * mult['f']; s_d = b_d * mult['d']; s_j = b_j * mult['j']
                if h in [0, 1, 2, 3, 4]: s_f *= 0.65; s_j *= 0.6; s_d *= 0.5
                if h in [5, 6]: s_f *= 0.8; s_j *= 0.8; s_d *= 0.8
                if h in [16, 17, 18, 19]: s_f *= 1.2; s_j *= 1.25; s_d *= 1.3
                
                s_sev = max(s_f, 0) + (max(s_d, 0) * 4) + (max(s_j, 0) / 120)
                sim_trajectory.append({'Hour': f"{h:02d}:00", 'ForecastSeverity': s_sev, 'Trajectory': f'{selected_severity} Simulation'})
            else:
                sim_trajectory.append({'Hour': f"{h:02d}:00", 'ForecastSeverity': b_sev, 'Trajectory': f'{selected_severity} Simulation'})

if selected_severity != "Observed Conditions":
    st.markdown("<br>### ⚖️ Operational Scenario Comparison", unsafe_allow_html=True)
    st.markdown("<div class='sim-warning'>Scenario values computationally amplified for operational comparison. Forecasting is disabled during simulation mode to preserve analytical realism.</div>", unsafe_allow_html=True)
else:
    st.markdown("<br>### 🔮 Next 4-Hour Mobility Forecast", unsafe_allow_html=True)
    st.caption("Based on observed historical mobility behavior")

combined_df = pd.DataFrame(baseline_trajectory + sim_trajectory) if selected_severity != "Observed Conditions" else pd.DataFrame(baseline_trajectory)
fig = px.line(combined_df, x="Hour", y="ForecastSeverity", color="Trajectory", markers=True, 
              color_discrete_sequence=['#00E5FF', '#FF006E'] if selected_severity != "Observed Conditions" else ['#00E5FF'])

if selected_severity != "Observed Conditions":
    fig.update_traces(line=dict(dash="dot"), selector=dict(name="Observed Baseline"))

current_hour_str = f"{target_h:02d}:00"
fig.add_vline(x=current_hour_str, line_width=1, line_dash="dash", line_color="white", opacity=0.5)
fig.add_annotation(x=current_hour_str, y=1, yref="paper", text="Active Hour", showarrow=False, font=dict(color="white", size=10), yshift=15)

fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                  yaxis_title="Severity Index", xaxis_title="", legend=dict(orientation="h", y=1.1, x=1),
                  margin=dict(t=30, b=0, l=0, r=0), height=400)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# =========================================================
# 9. ADVANCED MAPPING ENGINE 
# =========================================================
st.markdown("---")
st.markdown("## 🗺️ National Operational Posture")

m_df = df[df['Hour'] == target_h].groupby('City_UI')[['TrafficFrictionScore', 'TravelTimeInflationPct', 'JamLengthKm', 'TravelDelayMinutes', 'NetworkShockEscalation']].mean().reset_index()

m_df['TrafficFrictionScore'] *= mult['f']
m_df['TravelTimeInflationPct'] *= mult['p']
m_df['TravelDelayMinutes'] *= mult['d']
m_df['JamLengthKm'] *= mult['j']
m_df['NetworkShockEscalation'] *= mult['r']

if target_h in [0, 1, 2, 3, 4]: m_df['TrafficFrictionScore'] *= 0.65; m_df['TravelDelayMinutes'] *= 0.5
if target_h in [5, 6]: m_df['TrafficFrictionScore'] *= 0.8; m_df['TravelDelayMinutes'] *= 0.8
if target_h in [16, 17, 18, 19]: m_df['TrafficFrictionScore'] *= 1.2; m_df['TravelDelayMinutes'] *= 1.3

m_df['lat'] = m_df['City_UI'].map(lambda x: CITY_COORDS.get(x, {}).get('lat', 0))
m_df['lon'] = m_df['City_UI'].map(lambda x: CITY_COORDS.get(x, {}).get('lon', 0))

m_df['CityHourBaseline'] = m_df['City_UI'].apply(lambda c: max(df[(df['City_UI'] == c) & (df['Hour'] == target_h)]['TrafficFrictionScore'].mean(), 0.5))
m_df['OperationalSeverity'] = (((m_df['TrafficFrictionScore'].clip(lower=0) / m_df['CityHourBaseline']) * 15) + (m_df['TravelTimeInflationPct'].abs() * 2) + (m_df['TravelDelayMinutes'].clip(lower=0) * 8))

s_min, s_max = m_df['OperationalSeverity'].min(), m_df['OperationalSeverity'].max()
m_df['BubbleSize'] = ((m_df['OperationalSeverity'] - s_min) / ((s_max - s_min) + 0.01) * 55) + 10
m_df['Narrative'] = m_df.apply(lambda row: get_typology_diagnosis(row['TrafficFrictionScore'], row['TravelDelayMinutes'], row['JamLengthKm']), axis=1)

fig_map = px.scatter_mapbox(m_df, lat='lat', lon='lon', size='BubbleSize', color='OperationalSeverity', hover_name='City_UI',
    hover_data={'lat': False, 'lon': False, 'OperationalSeverity': False, 'BubbleSize': False, 'Narrative': True},
    color_continuous_scale=m_cols, zoom=6.2)
fig_map.update_traces(hovertemplate="<b style='font-size:16px'>%{hovertext}</b><br><br><b>State:</b> %{customdata[0]}<extra></extra>")
fig_map.update_layout(mapbox_style=m_style, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), height=550,
                      margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False, hoverlabel=dict(bgcolor="#161F2E", bordercolor="#FF006E", font_size=14))

st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})
st.caption("UAE Mobility Intelligence Console • Baseline Reality Edition" if selected_severity == "Observed Conditions" else "UAE Mobility Intelligence Console • Simulation Engine Active")