import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Absolute paths anchored to this file â€” immune to CWD issues
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DOTENV_PATH = r"C:\Users\DELL\Desktop\uae-traffic-friction-intelligence\.env"
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)

def get_api_key():
    """Read key directly from os.environ â€” dotenv already loaded it at startup."""
    # Try os.environ first (already populated by load_dotenv above)
    key = os.environ.get("TOMTOM_API_KEY", "").strip()
    if not key:
        # Fallback: re-read .env manually
        load_dotenv(dotenv_path=_DOTENV_PATH, override=True)
        key = os.environ.get("TOMTOM_API_KEY", "").strip()
    return key

TOMTOM_API_KEY = get_api_key()

# =========================================================
# 0. PLATFORM INITIALIZATION
# =========================================================
st.set_page_config(page_title="UAE Mobility Intelligence", page_icon="ðŸš¦", layout="wide")

# =========================================================
# 1. CONFIGURATION & METADATA LAYER
# =========================================================
CITY_COORDS = {
    'Dubai':         {'lat': 25.2048, 'lon': 55.2708},
    'Abu Dhabi':     {'lat': 24.4539, 'lon': 54.3773},
    'Sharjah':       {'lat': 25.3462, 'lon': 55.4209},
    'Ajman':         {'lat': 25.4052, 'lon': 55.5136},
    'Ras Al Khaimah':{'lat': 25.7895, 'lon': 55.9432},
    'Fujairah':      {'lat': 25.1288, 'lon': 56.3265},
    'Umm Al Quwain': {'lat': 25.5647, 'lon': 55.5534},
    'Al Ain':        {'lat': 24.1302, 'lon': 55.8023},
}

# UAE road-level corridor intelligence registry
# Structure: Region â†’ Corridor â†’ { RoadName: {lat, lon} }
# Each road is an independent TomTom flowSegmentData monitoring point
UAE_CORRIDORS = {
    "Dubai": {
        "Downtown Dubai": {
            "Financial Centre Rd":        {"lat": 25.2065, "lon": 55.2751},
            "Al Mustaqbal St":            {"lat": 25.1943, "lon": 55.2754},
            "Sheikh MBR Blvd":            {"lat": 25.1895, "lon": 55.2778},
            "Doha St (D89)":              {"lat": 25.2110, "lon": 55.2638},
        },
        "Dubai Marina": {
            "Jumeirah Beach Rd":          {"lat": 25.0868, "lon": 55.1326},
            "Al Sufouh Rd":               {"lat": 25.0943, "lon": 55.1503},
            "SZR (Marina Section)":       {"lat": 25.0798, "lon": 55.1467},
            "Al Marsa St":                {"lat": 25.0762, "lon": 55.1338},
        },
        "Deira": {
            "Al Rigga Rd":               {"lat": 25.2635, "lon": 55.3192},
            "Baniyas Rd":                {"lat": 25.2697, "lon": 55.3095},
            "Omar bin Al Khattab Rd":     {"lat": 25.2654, "lon": 55.3072},
            "Salah Al Din Rd":           {"lat": 25.2577, "lon": 55.3249},
        },
        "Business Bay": {
            "Al Khail Rd (Bay)":          {"lat": 25.1867, "lon": 55.2608},
            "Marasi Dr":                  {"lat": 25.1840, "lon": 55.2710},
            "Business Bay Bridge":        {"lat": 25.1932, "lon": 55.2770},
            "Al Asayel St":               {"lat": 25.1795, "lon": 55.2660},
        },
        "JLT": {
            "JLT Cluster Drive":          {"lat": 25.0657, "lon": 55.1388},
            "Al Asayel St (JLT)":         {"lat": 25.0720, "lon": 55.1440},
            "SZR (JLT Section)":          {"lat": 25.0613, "lon": 55.1354},
            "Jumeirah Islands Blvd":      {"lat": 25.0540, "lon": 55.1520},
        },
        "Dubai Airport": {
            "Airport Rd (D67)":           {"lat": 25.2532, "lon": 55.3657},
            "Al Garhoud Bridge":          {"lat": 25.2390, "lon": 55.3450},
            "Terminal 3 Access Rd":       {"lat": 25.2544, "lon": 55.3642},
            "Casablanca St":              {"lat": 25.2480, "lon": 55.3554},
        },
        "Sheikh Zayed Road": {
            "SZR (DIFC Section)":         {"lat": 25.2181, "lon": 55.2819},
            "SZR (World Trade Centre)":   {"lat": 25.2264, "lon": 55.2880},
            "SZR (Mall of Emirates)":     {"lat": 25.1190, "lon": 55.1990},
            "SZR (Al Safa)":              {"lat": 25.1550, "lon": 55.2300},
        },
    },
    "Abu Dhabi": {
        "Corniche": {
            "Corniche Rd East":           {"lat": 24.4864, "lon": 54.3548},
            "Corniche Rd West":           {"lat": 24.4762, "lon": 54.3437},
            "Hamdan St":                  {"lat": 24.4820, "lon": 54.3640},
            "Al Falah St":                {"lat": 24.4933, "lon": 54.3695},
        },
        "Yas Island": {
            "Yas Marina Circuit Rd":      {"lat": 24.4694, "lon": 54.6024},
            "Yas Island Blvd":            {"lat": 24.4959, "lon": 54.6079},
            "Ferrari World Access Rd":    {"lat": 24.4842, "lon": 54.6076},
            "Al Raha Beach Dr":           {"lat": 24.4603, "lon": 54.5958},
        },
        "Khalifa City": {
            "Khalifa City Main Rd":       {"lat": 24.4219, "lon": 54.5353},
            "Al Rahaâ€“Khalifa Rd":         {"lat": 24.4374, "lon": 54.5571},
            "Airport Rd South":           {"lat": 24.4110, "lon": 54.5800},
            "Khalifa City A Rd":          {"lat": 24.4310, "lon": 54.5192},
        },
        "Mussafah": {
            "Mussafah Industrial Rd":     {"lat": 24.3618, "lon": 54.5014},
            "ICAD-1 Rd":                  {"lat": 24.3432, "lon": 54.4890},
            "Mussafah Interchange":       {"lat": 24.3740, "lon": 54.5120},
            "Channel Rd Mussafah":        {"lat": 24.3510, "lon": 54.5200},
        },
        "Airport Corridor": {
            "Abu Dhabi Airport Rd (E10)": {"lat": 24.4330, "lon": 54.6511},
            "Sheikh Rashid Bin Saeed St": {"lat": 24.4516, "lon": 54.6229},
            "Salam St":                   {"lat": 24.4820, "lon": 54.3780},
            "Mohamed Bin Zayed City Rd":  {"lat": 24.4020, "lon": 54.5650},
        },
        "Al Reem Island": {
            "Al Reem Blvd":               {"lat": 24.5017, "lon": 54.4042},
            "Shams Abu Dhabi Rd":         {"lat": 24.5104, "lon": 54.4067},
            "Najmat Rd":                  {"lat": 24.5072, "lon": 54.3975},
            "Al Reem Bridge Access":      {"lat": 24.4981, "lon": 54.3912},
        },
    },
    "Sharjah": {
        "Al Majaz": {
            "Al Wahda St (SHJ)":          {"lat": 25.3412, "lon": 55.3912},
            "Al Majaz Corniche":          {"lat": 25.3391, "lon": 55.3878},
            "Khalid Lagoon Rd":           {"lat": 25.3320, "lon": 55.3820},
            "Al Khan Rd":                 {"lat": 25.3278, "lon": 55.3950},
        },
        "Rolla": {
            "Al Arouba Rd":               {"lat": 25.3500, "lon": 55.3947},
            "Al Rolla Rd":                {"lat": 25.3529, "lon": 55.3932},
            "Bank St (SHJ)":              {"lat": 25.3480, "lon": 55.3970},
            "Al Mutanabi St":             {"lat": 25.3551, "lon": 55.3989},
        },
        "Industrial Area": {
            "Industrial Rd 1":            {"lat": 25.3110, "lon": 55.4450},
            "Industrial Rd 4":            {"lat": 25.3208, "lon": 55.4499},
            "Al Wahda Rd (SHJ Ind)":      {"lat": 25.3300, "lon": 55.4350},
            "Sharjah Industrial Blvd":    {"lat": 25.3000, "lon": 55.4600},
        },
        "Buhaira": {
            "Buhaira Corniche":           {"lat": 25.3250, "lon": 55.3810},
            "Al Khalidiyah St":           {"lat": 25.3190, "lon": 55.3765},
            "Al Qasimia Rd":              {"lat": 25.3310, "lon": 55.3700},
            "Corniche Al Buhaira":        {"lat": 25.3168, "lon": 55.3842},
        },
        "Al Nahda": {
            "Al Nahda St":                {"lat": 25.2918, "lon": 55.3891},
            "Al Nahda (SHJâ€“Dubai Bdr)":   {"lat": 25.2870, "lon": 55.3820},
            "Maliha Rd":                  {"lat": 25.2800, "lon": 55.4000},
            "Al Yarmook St":              {"lat": 25.2980, "lon": 55.3940},
        },
        "King Faisal Road": {
            "King Faisal Rd (North)":     {"lat": 25.3620, "lon": 55.4010},
            "King Faisal Rd (Central)":   {"lat": 25.3548, "lon": 55.4021},
            "Al Dhaid Rd Junction":       {"lat": 25.3450, "lon": 55.4100},
            "Al Zahra St":                {"lat": 25.3670, "lon": 55.4060},
        },
    },
    "Ajman": {
        "Ajman Downtown": {
            "Sheikh Humaid Bin Rashid St": {"lat": 25.4109, "lon": 55.4354},
            "Al Sawan St":                {"lat": 25.4052, "lon": 55.4280},
            "Al Rumailah Rd":             {"lat": 25.4178, "lon": 55.4220},
            "Ajman Corniche":             {"lat": 25.4189, "lon": 55.4380},
        },
        "Sheikh Humaid Road": {
            "Sheikh Humaid Rd (North)":   {"lat": 25.4138, "lon": 55.4447},
            "Sheikh Humaid Rd (South)":   {"lat": 25.3980, "lon": 55.4500},
            "Al Jurf Industrial":         {"lat": 25.4052, "lon": 55.4550},
            "Al Rawdha Rd":               {"lat": 25.4200, "lon": 55.4620},
        },
        "Al Rashidiya": {
            "Al Rashidiya St":            {"lat": 25.4178, "lon": 55.4782},
            "Ajmanâ€“UAQ Rd (South)":       {"lat": 25.4120, "lon": 55.4850},
            "Al Muntazah St":             {"lat": 25.4250, "lon": 55.4750},
            "New Industrial Rd":          {"lat": 25.4050, "lon": 55.4900},
        },
        "Ajman Port Area": {
            "Ajman Port Rd":              {"lat": 25.4237, "lon": 55.4295},
            "Port Authority Rd":          {"lat": 25.4260, "lon": 55.4330},
            "Al Ittihad St":              {"lat": 25.4120, "lon": 55.4310},
            "Ajman Free Zone Rd":         {"lat": 25.4070, "lon": 55.4380},
        },
    },
    "Ras Al Khaimah": {
        "RAK City Centre": {
            "Al Nakheel Rd":              {"lat": 25.7895, "lon": 55.9432},
            "Sheikh M. Bin Salem Rd":     {"lat": 25.7970, "lon": 55.9570},
            "Oman St (RAK)":              {"lat": 25.7820, "lon": 55.9380},
            "Al Quwain Rd":               {"lat": 25.8010, "lon": 55.9490},
        },
        "Al Nakheel": {
            "Al Nakheel Corniche":        {"lat": 25.8112, "lon": 55.9760},
            "Al Nakheel Beach Rd":        {"lat": 25.8200, "lon": 55.9820},
            "Al Hamra Rd":                {"lat": 25.7640, "lon": 55.9220},
            "Al Nakheel Rd (South)":      {"lat": 25.8050, "lon": 55.9690},
        },
        "Al Qawasim": {
            "Qawasim Corniche":           {"lat": 25.7730, "lon": 55.9518},
            "Al Muntasir Rd":             {"lat": 25.7680, "lon": 55.9450},
            "Old Al Qawasim Rd":          {"lat": 25.7790, "lon": 55.9350},
            "Al Saqr St":                 {"lat": 25.7850, "lon": 55.9410},
        },
        "RAK Airport Road": {
            "RAKâ€“Dubai Rd (E11)":         {"lat": 25.8345, "lon": 55.9388},
            "RAK Airport Access":         {"lat": 25.8445, "lon": 55.9310},
            "Al Rams Rd":                 {"lat": 25.8900, "lon": 55.9500},
            "Al Jeer Rd":                 {"lat": 25.8650, "lon": 55.9480},
        },
    },
    "Fujairah": {
        "Fujairah City": {
            "Hamad Bin Abdullah Rd":      {"lat": 25.1288, "lon": 56.3265},
            "Sheikh M. Bin Hamad Rd":     {"lat": 25.1220, "lon": 56.3340},
            "Al Faseel Rd (City)":        {"lat": 25.1350, "lon": 56.3380},
            "Al Gurfa Rd":                {"lat": 25.1148, "lon": 56.3462},
        },
        "Fujairah Port": {
            "Port Industrial Rd":         {"lat": 25.1091, "lon": 56.3473},
            "Port Authority Rd (FUJ)":    {"lat": 25.1050, "lon": 56.3510},
            "Container Terminal Rd":      {"lat": 25.1020, "lon": 56.3560},
            "Port Access Rd South":       {"lat": 25.0980, "lon": 56.3490},
        },
        "Al Faseel Road": {
            "Al Faseel Rd (North)":       {"lat": 25.1450, "lon": 56.3530},
            "Al Faseel Rd (Central)":     {"lat": 25.1372, "lon": 56.3498},
            "Al Faseel Rd (South)":       {"lat": 25.1270, "lon": 56.3470},
            "Al Faseel Beach Rd":         {"lat": 25.1510, "lon": 56.3560},
        },
        "Dibba Road": {
            "Dibbaâ€“Fujairah Rd (E89)":    {"lat": 25.2102, "lon": 56.3601},
            "Al Aqah Beach Rd":           {"lat": 25.3080, "lon": 56.3550},
            "E99 Fujairahâ€“Kalba Rd":      {"lat": 25.0500, "lon": 56.3580},
            "Masafi Junction Rd":         {"lat": 25.3200, "lon": 56.1460},
        },
    },
    "Umm Al Quwain": {
        "UAQ City": {
            "King Faisal Rd (UAQ)":       {"lat": 25.5647, "lon": 55.5534},
            "Sheikh Ahmad Bin Rashid Rd": {"lat": 25.5701, "lon": 55.5505},
            "Old Town Rd (UAQ)":          {"lat": 25.5620, "lon": 55.5550},
            "Al Raas Rd":                 {"lat": 25.5768, "lon": 55.5590},
        },
        "UAQ Marina": {
            "UAQ Marine Club Rd":         {"lat": 25.5701, "lon": 55.5620},
            "UAQ Corniche":               {"lat": 25.5750, "lon": 55.5510},
            "UAQ Beach Rd":               {"lat": 25.5640, "lon": 55.5420},
            "Falaj Al Mualla Rd":         {"lat": 25.5480, "lon": 55.5670},
        },
        "King Faisal Rd UAQ": {
            "King Faisal Rd (North UAQ)": {"lat": 25.5800, "lon": 55.5460},
            "King Faisal Rd (Central)":   {"lat": 25.5593, "lon": 55.5689},
            "UAQâ€“Ajman Junction":         {"lat": 25.5350, "lon": 55.5850},
            "UAQâ€“RAK Junction":           {"lat": 25.6050, "lon": 55.5220},
        },
    },
    "Al Ain": {
        "Al Ain City Centre": {
            "Sultan Bin Zayed St":        {"lat": 24.2075, "lon": 55.7447},
            "Khalifa St (Al Ain)":        {"lat": 24.2180, "lon": 55.7560},
            "Zayed Bin Sultan St":        {"lat": 24.1980, "lon": 55.7620},
            "Al Ain Central Rd":          {"lat": 24.2130, "lon": 55.7480},
        },
        "Al Jimi": {
            "Al Jimi Rd":                 {"lat": 24.2330, "lon": 55.7432},
            "Al Jimi Mall Access Rd":     {"lat": 24.2390, "lon": 55.7510},
            "Khalifa Bin Zayed St (Jimi)":{"lat": 24.2270, "lon": 55.7350},
            "Al Ain North Rd":            {"lat": 24.2450, "lon": 55.7380},
        },
        "Al Ain Oasis": {
            "Zayed Al Awwal St":          {"lat": 24.2119, "lon": 55.7626},
            "Al Ain Oasis Rd":            {"lat": 24.2080, "lon": 55.7700},
            "Al Mutawaa Rd":              {"lat": 24.2010, "lon": 55.7580},
            "Al Khabisi Rd":              {"lat": 24.2150, "lon": 55.7810},
        },
        "Al Ain Airport Rd": {
            "Al Ain Airport Access":      {"lat": 24.2618, "lon": 55.6094},
            "Al Ainâ€“Abu Dhabi Rd (E22)":  {"lat": 24.2200, "lon": 55.6500},
            "Al Ain Bypass Rd":           {"lat": 24.2000, "lon": 55.6200},
            "Al Foah Rd":                 {"lat": 24.2800, "lon": 55.7100},
        },
    },
}

# =========================================================
# 2. PREMIUM CSS
# =========================================================
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* Base */
    .stApp { background-color: #0A0F1C !important; color: #F8FAFC !important; font-family: 'Inter', sans-serif !important; }
    body { font-size: 16px; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #101826 0%, #0B111C 100%) !important; border-right: 1px solid #1E293B !important; }
    div[data-baseweb="select"] { background-color: #161F2E !important; border: 1px solid #263244 !important; border-radius: 8px !important; }
    div[data-baseweb="select"] * { background-color: #161F2E !important; color: white !important; }

    /* KPI Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #131C2C, #101826) !important;
        border: 1px solid #1F2A3D !important; padding: 14px 12px !important;
        border-radius: 12px !important; min-width: 0;
        transition: border-color 0.2s, transform 0.2s;
    }
    div[data-testid="metric-container"]:hover { border: 1px solid #3A86FF !important; transform: translateY(-2px) !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.72rem !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px !important; color: #94A3B8 !important; }
    div[data-testid="stMetricValue"] { font-size: 1.25rem !important; font-weight: 800 !important; line-height: 1.2 !important; white-space: normal !important; word-wrap: break-word !important; }
    div[data-testid="stMetricDelta"] { font-size: 0.72rem !important; margin-top: 6px !important; }

    /* Live mode KPI card accent */
    .live-metric-row div[data-testid="metric-container"] {
        border: 1px solid rgba(255, 0, 110, 0.22) !important;
        background: linear-gradient(145deg, #1A0D18, #140B14) !important;
    }
    .live-metric-row div[data-testid="metric-container"]:hover { border: 1px solid #FF006E !important; }

    .element-container:has(.js-plotly-plot) {
        background: linear-gradient(145deg, #111827, #0F172A) !important;
        padding: 16px !important; border-radius: 12px !important; border: 1px solid #1F2937 !important;
    }
    hr { border-color: #1E293B !important; margin: 2rem 0 !important; }
    .sim-warning { color: #FF8FA3; font-size: 0.80rem; margin-top: -5px; margin-bottom: 10px; opacity: 0.8; }

    /* Environmental context */
    .weather-context {
        background-color: rgba(0, 229, 255, 0.05);
        border-left: 3px solid #00E5FF;
        padding: 10px 14px; margin-top: 15px;
        border-radius: 0 4px 4px 0;
        font-size: 0.88rem; color: #E2E8F0; line-height: 1.5;
    }
    .weather-context strong { color: #00E5FF; }
    .live-badge {
        background-color: #FF006E; color: white;
        padding: 2px 6px; border-radius: 4px;
        font-size: 0.68rem; font-weight: 800;
        margin-left: 6px; vertical-align: middle; letter-spacing: 0.05em;
    }

    /* Live Status Strip */
    .live-status-strip {
        background: linear-gradient(90deg, rgba(255,0,110,0.13) 0%, rgba(255,0,110,0.04) 100%);
        border: 1px solid rgba(255,0,110,0.28);
        border-radius: 9px; padding: 12px 16px;
        margin-bottom: 18px;
        display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
        font-size: 0.82rem; color: #CBD5E1;
    }
    .live-status-dot {
        width: 9px; height: 9px; border-radius: 50%;
        background: #FF006E; display: inline-block; flex-shrink: 0;
        animation: pulse-dot 1.6s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,0,110,0.55); }
        50%       { opacity: 0.7; box-shadow: 0 0 0 6px rgba(255,0,110,0); }
    }

    /* Live pulse badge */
    .live-pulse {
        display: inline-block; background: #FF006E; color: white;
        padding: 2px 9px; border-radius: 4px;
        font-size: 0.62rem; font-weight: 800; letter-spacing: 0.10em;
        animation: pulse-dot 1.6s ease-in-out infinite;
        vertical-align: middle;
    }

    /* Road closure alert */
    .closure-alert {
        background: rgba(255, 0, 110, 0.11);
        border: 1px solid rgba(255, 0, 110, 0.45);
        border-radius: 8px; padding: 12px 18px;
        font-size: 0.88rem; color: #FCA5A5;
        margin-bottom: 16px;
        display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    }
    .live-offline {
        background: rgba(255, 0, 110, 0.06);
        border-left: 3px solid #FF006E;
        padding: 14px 18px; border-radius: 0 8px 8px 0;
        font-size: 0.88rem; color: #94A3B8; margin-top: 8px;
    }
    .live-state-panel {
        background: linear-gradient(145deg, #111827, #0F172A);
        border: 1px solid #1F2937;
        border-radius: 12px; padding: 20px 22px;
        height: 100%; min-height: 260px;
    }
    .live-label {
        font-size: 0.68rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.09em;
        color: #64748B; margin-bottom: 10px;
    }
    .live-metric-divider { border-top: 1px solid #1E293B; margin: 13px 0; }

    /* Mobile filter expander - shown on narrow screens */
    .mobile-filter-hint { display: none; }

    /* -----------------------------------------------------
       MOBILE-FIRST RESPONSIVE OVERRIDES (<= 768 px)
    ----------------------------------------------------- */
    @media screen and (max-width: 768px) {

        /* Container padding tightened for phone screens */
        .block-container {
            padding-left: 10px !important;
            padding-right: 10px !important;
            padding-top: 48px !important;
            padding-bottom: 80px !important;  /* room for bottom nav */
            max-width: 100% !important;
        }

        /* Sidebar hidden - controls live in the inline expander */
        section[data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Show the mobile filter hint */
        .mobile-filter-hint { display: block !important; }

        /* Stack every st.columns() layout */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 10px !important;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        /* KPI Cards - larger, full-width, thumb-friendly */
        div[data-testid="metric-container"] {
            padding: 18px 16px !important;
            border-radius: 14px !important;
            margin-bottom: 8px !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 800 !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 0.76rem !important;
        }

        /* Executive Intelligence cards */
        [data-testid="column"] > div > div[style*="border-radius:10px"] {
            padding: 16px !important;
            margin-bottom: 10px !important;
        }

        /* Plotly charts full width, touch-friendly */
        .js-plotly-plot, .plotly, .plot-container {
            width: 100% !important;
            touch-action: pan-y !important;
        }
        .element-container:has(.js-plotly-plot) {
            padding: 10px !important;
            border-radius: 10px !important;
        }

        /* Title */
        h1 { font-size: 1.4rem !important; margin-bottom: 8px !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.0rem !important; }

        /* Weather context */
        .weather-context {
            font-size: 0.92rem !important;
            padding: 12px 14px !important;
            line-height: 1.55 !important;
        }

        /* Live status strip */
        .live-status-strip {
            font-size: 0.86rem !important;
            padding: 12px 14px !important;
            gap: 8px !important;
        }

        /* Table - mobile-scrollable */
        div[style*="overflow-x:auto"] table {
            font-size: 0.78rem !important;
        }
        div[style*="overflow-x:auto"] {
            -webkit-overflow-scrolling: touch !important;
        }

        /* Live header typography */
        div[style*="font-size:0.85rem"] { font-size: 0.90rem !important; }
        div[style*="font-size:0.67rem"] { font-size: 0.72rem !important; }

        /* Deviation intelligence panel grid - stack */
        div[style*="grid-template-columns:1fr 1fr 1fr 1.4fr"] {
            grid-template-columns: 1fr 1fr !important;
            gap: 14px !important;
        }

        /* Expander touch target */
        [data-testid="stExpander"] summary {
            min-height: 48px !important;
            font-size: 0.95rem !important;
            padding: 12px 16px !important;
        }

        /* Selectboxes */
        div[data-baseweb="select"] {
            min-height: 44px !important;
            font-size: 0.95rem !important;
        }

        /* Sidebar-replacement expander styling */
        [data-testid="stExpander"] {
            background: linear-gradient(145deg, #131C2C, #101826) !important;
            border: 1px solid #1F2A3D !important;
            border-radius: 12px !important;
            margin-bottom: 14px !important;
        }
    }

    /* -----------------------------------------------------
       TABLET (769px - 1024px)
    ----------------------------------------------------- */
    @media screen and (min-width: 769px) and (max-width: 1024px) {
        .block-container {
            padding-left: 16px !important;
            padding-right: 16px !important;
        }
        div[data-testid="stMetricValue"] { font-size: 1.35rem !important; }

        /* 4-column KPI row -> 2x2 grid on tablet */
        .live-metric-row [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        .live-metric-row [data-testid="column"] {
            flex: 1 1 48% !important;
            min-width: 48% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. DATA INGESTION
# =========================================================
@st.cache_data
def load_data():
    _csv_candidates = [
        os.path.join(_SCRIPT_DIR, "..", "data", "processed", "uae_traffic_intelligence_master.csv"),
        os.path.join(_SCRIPT_DIR, "..", "data", "uae_traffic_intelligence_master.csv"),
        "data/uae_traffic_intelligence_master.csv",
    ]
    data = None
    for path in _csv_candidates:
        try:
            data = pd.read_csv(path)
            break
        except FileNotFoundError:
            continue
    if data is None:
        st.error("Could not locate the traffic master CSV. Check data/processed/ directory.")
        st.stop()
    data['City_UI'] = data['City'].str.replace('-', ' ').str.title().replace(
        {'Abu Dhabi': 'Abu Dhabi', 'Ras Al Khaimah': 'Ras Al Khaimah'})
    return data

df = load_data()

@st.cache_data(ttl=900)
def fetch_live_weather(lat, lon):
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&timezone=auto")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()['current']
        return None
    except:
        return None

def fetch_tomtom_flow(lat, lon):
    """Fetch live traffic flow segment data from TomTom Traffic API."""
    api_key = get_api_key()
    if not api_key or api_key == "your_tomtom_api_key_here":
        return None
    try:
        url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        params = {"point": f"{lat},{lon}", "unit": "KMPH", "key": api_key}
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            return resp.json().get("flowSegmentData")
        return None
    except Exception:
        return None

def fetch_corridor_telemetry(corridor_roads: dict) -> list:
    """Fetch independent TomTom telemetry for every road in a corridor.
    Returns list of per-road result dicts with parsed KPIs."""
    results = []
    for road_name, coords in corridor_roads.items():
        flow = fetch_tomtom_flow(coords["lat"], coords["lon"])
        if flow is None:
            continue
        cs      = flow.get("currentSpeed", 0)
        ff      = max(flow.get("freeFlowSpeed", 1), 1)
        ctt     = flow.get("currentTravelTime", 0)
        fftt    = max(flow.get("freeFlowTravelTime", 1), 1)
        conf    = flow.get("confidence", 0)
        closure = flow.get("roadClosure", False)
        geo     = flow.get("coordinates", {}).get("coordinate", [])
        state, color = classify_live_state(cs, ff, closure)
        results.append({
            "road":           road_name,
            "current_speed":  cs,
            "free_flow_speed":ff,
            "congestion_pct": get_live_congestion_pct(cs, ff),
            "delay_min":      get_live_delay_min(ctt, fftt),
            "state":          state,
            "state_color":    color,
            "confidence":     conf,
            "road_closure":   closure,
            "lat":            coords["lat"],
            "lon":            coords["lon"],
            "geo_coords":     geo,
        })
    return results

# =========================================================
# 4. DIAGNOSTIC TYPOLOGY & INTELLIGENCE FUNCTIONS
# =========================================================
def get_typology_diagnosis(f, d, j):
    if f > 10 and d > 2.0 and j > 450: return "Severe Congestion Pressure"
    if f > 7  and d > 1.5 and j > 250: return "Widespread Congestion"
    if f > 4  and d > 1.0 and j > 120: return "Heavy Traffic Conditions"
    if f > 2  and d > 0.5 and j > 40:  return "Moderate Traffic Build-Up"
    return "Smooth Traffic Flow"

def get_weather_interpretation(w_code, temp, wind):
    """Simplified, operational weather interpretation."""
    if wind > 30:
        return "Operational Caution", "Windy conditions. Potential crosswinds on open corridors."
    elif w_code in [45, 48]:
        return "Visibility Risk", "Fog or dust detected. Reduced visibility expected."
    elif w_code >= 51:
        return "Slowdown Risk", "Precipitation detected. Wet surface friction."
    elif w_code in [2, 3]:
        return "Stable Conditions", "Cloudy sky. Nominal impact on mobility."
    else:
        return "Good Conditions", "Clear weather. Favourable operational environment."

def get_speed_interpretation(raw_p, raw_d):
    if abs(raw_d) < 1.0: return "Near Baseline",           "Nominal variance",        "off"
    if abs(raw_p) < 1:   return "Normal Flow",             "Within baseline",         "off"
    if raw_p > 0:        return f"{abs(raw_p):.1f}% Slower", "Traffic slowdown",      "inverse"
    return                      f"{abs(raw_p):.1f}% Faster", "Traffic flowing well",  "normal"

def get_delay_interpretation(norm_d):
    if norm_d < 0.5: return "Minimal Delay",          "Roads stable",          "normal"
    if norm_d < 2:   return f"{norm_d:.1f} Min Delay", "Moderate slowdown",    "inverse"
    return                   f"{norm_d:.1f} Min Delay", "Heavy commuter impact","inverse"

def get_queue_interpretation(norm_j):
    if norm_j < 40:  return f"{norm_j:.1f} KM", "Light buildup",               "normal"
    if norm_j < 120: return f"{norm_j:.1f} KM", "Moderate queue pressure",     "inverse"
    return                   f"{norm_j:.1f} KM", "Widespread congestion buildup","inverse"

def get_risk_interpretation(risk_score):
    if risk_score < 5:  return "Low",      "Stable mobility",         "normal"
    if risk_score < 15: return "Moderate", "Localized instability",   "inverse"
    if risk_score < 30: return "High",     "Escalation possible",     "inverse"
    return                     "Severe",   "Major congestion pressure","inverse"

def classify_live_state(current_speed, free_flow_speed, road_closure):
    """Classify live corridor operational state from speed ratio."""
    if road_closure:         return "Critical Road Closure",     "#FF006E"
    if free_flow_speed == 0: return "Data Unavailable",          "#94A3B8"
    ratio = current_speed / free_flow_speed
    if ratio >= 0.85: return "Smooth Traffic Flow",           "#00E5FF"
    if ratio >= 0.65: return "Moderate Traffic Build-Up",     "#FFD600"
    if ratio >= 0.40: return "Severe Congestion Pressure",    "#FF8F00"
    return                   "Critical Congestion",           "#FF006E"

def get_live_congestion_pct(current_speed, free_flow_speed):
    if free_flow_speed == 0: return 0.0
    return max(0.0, (1 - current_speed / free_flow_speed) * 100)

def get_live_delay_min(current_tt, free_flow_tt):
    return max(0.0, (current_tt - free_flow_tt) / 60.0)

# â”€â”€ Operational intelligence functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_corridor_pressure_index(agg_cong, peak_delay, n_live, n_total, any_closure):
    """Composite 0-100 corridor stress score. Explainable, telemetry-driven."""
    cong_score    = min(agg_cong * 1.4, 100)            # 0-100 from % congestion
    delay_score   = min(peak_delay * 9, 100)             # 0-100 from peak delay
    avail_penalty = (1 - n_live / max(n_total, 1)) * 40  # penalty for offline roads
    closure_score = 30 if any_closure else 0             # closure = major stress event
    pressure = (cong_score * 0.45 + delay_score * 0.30 +
                avail_penalty * 0.10 + closure_score * 0.15)
    return min(int(round(pressure)), 100)

def get_pressure_color(idx):
    if idx <= 25: return "#00E5FF"
    if idx <= 50: return "#FFD600"
    if idx <= 75: return "#FF8F00"
    return "#FF006E"

def get_confidence_tier(avg_conf, n_live, n_total):
    """Classify telemetry quality from confidence + road completeness."""
    completeness = n_live / max(n_total, 1)
    combined     = avg_conf * 0.70 + completeness * 0.30
    if combined >= 0.88: return "High Confidence",   "#00E5FF"
    if combined >= 0.65: return "Medium Confidence", "#FFD600"
    return                     "Low Confidence",     "#FF8F00"

_REGION_TO_CITY = {
    "Dubai": "Dubai", "Abu Dhabi": "Abu Dhabi",
    "Ras Al Khaimah": "Ras Al Khaimah", "Al Ain": "Al Ain",
    "Fujairah": "Fujairah",
    "Sharjah": "Dubai",                 # Baseline proxy
    "Ajman": "Dubai",                   # Baseline proxy
    "Umm Al Quwain": "Ras Al Khaimah"   # Baseline proxy
}

def get_baseline_comparison(df, region, target_h, live_cs, live_ff):
    """Compare live speed ratio vs historical baseline for same city + hour."""
    city = _REGION_TO_CITY.get(region)
    if not city:
        return None
    h_df = df[(df['City_UI'] == city) & (df['Hour'] == target_h)]
    if len(h_df) == 0:
        return None
    infl = h_df['TravelTimeInflationPct'].mean()          # e.g. 15 â†’ 15% above free-flow
    hist_delay = h_df['TravelDelayMinutes'].mean()
    expected_ratio = 1.0 / max(1.0 + infl / 100.0, 0.5)  # speed ratio implied by inflation
    expected_speed = live_ff * expected_ratio              # apply to live free-flow speed
    live_ratio     = live_cs / max(live_ff, 1)
    variance_pct   = (live_ratio - expected_ratio) / max(expected_ratio, 0.01) * 100
    if variance_pct > 10:     dev_label, dev_color = "Better Than Baseline",           "#00E5FF"
    elif variance_pct > -10:  dev_label, dev_color = "Within Historical Baseline",     "#94A3B8"
    elif variance_pct > -25:  dev_label, dev_color = "Elevated Corridor Pressure",     "#FFD600"
    elif variance_pct > -40:  dev_label, dev_color = "Significant Operational Deviation", "#FF8F00"
    else:                     dev_label, dev_color = "Critical Operational Deviation", "#FF006E"
    return {
        "expected_speed":  round(expected_speed, 1),
        "expected_ratio":  expected_ratio,
        "expected_infl":   infl,
        "hist_delay":      hist_delay,
        "live_ratio":      live_ratio,
        "variance_pct":    variance_pct,
        "dev_label":       dev_label,
        "dev_color":       dev_color,
        "city":            city,
        "n_samples":       len(h_df),
    }


# =========================================================
# 5. SIDEBAR - OPERATIONS CONSOLE
# =========================================================
st.sidebar.title("UAE Mobility Intelligence")
selected_city = st.sidebar.selectbox("Target Sector", options=sorted(df['City_UI'].unique()))

st.sidebar.markdown("### Operational Controls")

# Scenario and Live toggle are grouped - both are operational state controls
selected_severity = st.sidebar.selectbox(
    "Scenario",
    options=["Observed Conditions", "Low", "Moderate", "High", "Severe"]
)
if selected_severity != "Observed Conditions":
    st.sidebar.markdown("<small style='color:#FF006E; font-weight:600;'>Simulation Mode Active</small>", unsafe_allow_html=True)

live_enabled = st.sidebar.toggle("Enable Live Telemetry", key="live_toggle")

selected_region  = None
selected_sector  = None
if live_enabled:
    # Step 1 - Region selector (all UAE emirates)
    _live_regions = list(UAE_CORRIDORS.keys())
    selected_region = st.sidebar.selectbox(
        "Region",
        options=_live_regions,
        key="live_region"
    )
    # Step 2 - Corridor selector filtered to selected region only
    _region_corridors = list(UAE_CORRIDORS[selected_region].keys())
    selected_sector = st.sidebar.selectbox(
        "Corridor",
        options=_region_corridors,
        key="live_sector"
    )

# Time Window - only relevant in historical mode
# Live mode uses real-time, so the hour selector is hidden
if not live_enabled:
    st.sidebar.markdown("### Time Window")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        h_clock = st.selectbox("Hour", options=[12,1,2,3,4,5,6,7,8,9,10,11],
                                format_func=lambda x: f"{x}:00", label_visibility="collapsed")
    with c2:
        period = st.selectbox("Period", options=["AM", "PM"], label_visibility="collapsed")
    target_h = h_clock + (12 if period == "PM" and h_clock != 12 else 0)
    if period == "AM" and h_clock == 12: target_h = 0
else:
    # Live mode: anchor historical context to current hour
    target_h = datetime.now().hour
    period   = "PM" if target_h >= 12 else "AM"

m_style = "carto-darkmatter" if (live_enabled or period == "PM") else "carto-positron"
m_cols  = ['#00E5FF', '#7C3AED', '#FF006E']

# =========================================================
# 6. OPERATIONAL FILTERING + SCENARIO ENGINE
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
hour_factor   = max(hour_baseline, 0.5)

scenario_multipliers = {
    "Observed Conditions": {"f": 1.0, "p": 1.0, "j": 1.0, "d": 1.0, "r": 1.0},
    "Low":      {"f": 0.7,  "p": 0.7,  "j": 0.7,  "d": 0.7,  "r": 0.6},
    "Moderate": {"f": 1.0,  "p": 1.0,  "j": 1.0,  "d": 1.0,  "r": 1.0},
    "High":     {"f": 1.35, "p": 1.45, "j": 1.5,  "d": 1.4,  "r": 1.5},
    "Severe":   {"f": 1.8,  "p": 2.0,  "j": 2.2,  "d": 2.0,  "r": 2.0},
}
mult = scenario_multipliers[selected_severity]

raw_f = base_f * mult['f']; raw_p = base_p * mult['p']
raw_j = base_j * mult['j']; raw_d = base_d * mult['d']
raw_r = base_r * mult['r']

if target_h in [0, 1, 2, 3, 4]:   raw_f *= 0.65; raw_j *= 0.6;  raw_d *= 0.5; raw_r *= 0.55
if target_h in [5, 6]:             raw_f *= 0.8;  raw_j *= 0.8;  raw_d *= 0.8
if target_h in [16, 17, 18, 19]:   raw_f *= 1.2;  raw_j *= 1.25; raw_d *= 1.3; raw_r *= 1.2

norm_f = max(raw_f, 0); norm_d = max(raw_d, 0); norm_j = max(raw_j, 0)
context_f = norm_f / hour_factor

f_state                    = get_typology_diagnosis(norm_f, norm_d, norm_j)
p_display, p_delta, p_color = get_speed_interpretation(raw_p, raw_d)
d_display, d_delta, d_color = get_delay_interpretation(norm_d)
j_display, j_delta, j_color = get_queue_interpretation(norm_j)

risk_score = min(max(raw_r, 0) * (((context_f * 0.8) + (norm_d * 1.2) + (norm_j / 180)) / 6), 100)
r_display, r_delta, r_color = get_risk_interpretation(risk_score)

congestion_label = (
    "Localized"     if norm_j < 40   else
    "Moderate"      if norm_j < 120  else
    "Widespread"    if norm_j < 250  else
    "Network-Wide"
)

# Weather: use live region coords if live mode, else selected city
_weather_coords = (
    CITY_COORDS.get(selected_region, CITY_COORDS.get(selected_city, {'lat': 25.2048, 'lon': 55.2708}))
    if live_enabled and selected_region
    else CITY_COORDS.get(selected_city, {'lat': 25.2048, 'lon': 55.2708})
)
w_data = fetch_live_weather(_weather_coords['lat'], _weather_coords['lon'])
weather_state, weather_context = "Nominal", "Live environmental telemetry unavailable."
if w_data:
    weather_state, weather_context = get_weather_interpretation(
        w_data['weather_code'], w_data['temperature_2m'], w_data['wind_speed_10m'])

# =========================================================
# 7. MOBILE QUICK-ACCESS STATUS BAR
# =========================================================
# On mobile, the sidebar is accessible via the hamburger menu (top-left).
# This compact bar shows the current active mode and location for orientation.
st.markdown("<div class='mobile-filter-hint'>", unsafe_allow_html=True)
_mob_mode = "LIVE" if live_enabled else "HISTORICAL"
_mob_loc  = f"{selected_sector}, {selected_region}" if live_enabled and selected_sector else selected_city
st.markdown(
    f"<div style='background:rgba(255,0,110,0.08); border:1px solid rgba(255,0,110,0.25); "
    f"border-radius:10px; padding:10px 14px; margin-bottom:12px; display:flex; "
    f"align-items:center; gap:10px; font-size:0.85rem;'>"
    f"<span style='background:#FF006E; color:white; padding:2px 8px; border-radius:4px; "
    f"font-size:0.70rem; font-weight:800; letter-spacing:0.06em;'>{_mob_mode}</span>"
    f"<span style='color:#CBD5E1; flex:1;'>{_mob_loc}</span>"
    f"<span style='color:#475569; font-size:0.72rem;'>Tap menu to change</span>"
    f"</div>",
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 8. TITLE & LIVE STATUS STRIP
# =========================================================
st.title("UAE Mobility Intelligence")

if live_enabled and selected_sector:
    now_ts = datetime.now().strftime("%H:%M:%S")
    st.markdown(
        f"""
        <div class='live-status-strip'>
            <span class='live-status-dot'></span>
            <span>
                <strong style='color:#F8FAFC; letter-spacing:0.04em;'>LIVE ROADWAY CONDITIONS ACTIVE</strong>
                &nbsp;&nbsp;·&nbsp;&nbsp;
                TomTom Traffic Telemetry
                &nbsp;&nbsp;·&nbsp;&nbsp;
                Corridor: <strong style='color:#FF006E;'>{selected_sector}</strong>, {selected_region}
                &nbsp;&nbsp;·&nbsp;&nbsp;
                Auto-refresh every 120 seconds
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span style='color:#475569;'>{now_ts}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# 8. HISTORICAL NETWORK STATUS KPIs (hidden in live mode)
# =========================================================
if not live_enabled:
    st.markdown("## Network Status")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Network State",     f_state,          f"Relative Load {context_f:.1f}x",         delta_color="off")
    k2.metric("Travel Speed",      p_display,        p_delta,                                    delta_color=p_color)
    k3.metric("Congestion Spread", congestion_label, f"~{norm_j:.0f} km affected roadway",       delta_color=j_color)
    k4.metric("Delay Impact",      d_display,        d_delta,                                    delta_color=d_color)
    k5.metric("Gridlock Risk",     r_display,        r_delta,                                    delta_color=r_color)


# =========================================================
# 9. LIVE CORRIDOR TELEMETRY MODULE
#    Shown when live is ON â€” replaces forecast & posture map
# =========================================================
if live_enabled and selected_sector:

    # Auto-refresh every 120 seconds
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=120_000, key="live_refresh")
    except ImportError:
        pass

    st.markdown("---")

    corridor_roads = UAE_CORRIDORS[selected_region][selected_sector]
    n_total        = len(corridor_roads)

    # â”€â”€ API key check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _live_key = get_api_key()
    if not _live_key or _live_key == "your_tomtom_api_key_here":
        st.markdown(
            "<div class='live-offline'>âš ï¸ <strong>Live telemetry offline</strong> â€” "
            "<code>TOMTOM_API_KEY</code> not configured. Add your key to <code>.env</code> "
            "at the project root to enable roadway telemetry.</div>",
            unsafe_allow_html=True
        )
    else:
        # â”€â”€ Fetch all roads in corridor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        with st.spinner(f"Fetching live telemetry â€” {n_total} roadways in {selected_sector}â€¦"):
            road_results = fetch_corridor_telemetry(corridor_roads)

        if not road_results:
            st.markdown(
                "<div class='live-offline'>âš ï¸ <strong>Unable to reach TomTom Traffic API.</strong> "
                "Live corridor telemetry temporarily unavailable. Will retry on next auto-refresh (120 sec).</div>",
                unsafe_allow_html=True
            )
        else:
            n_live = len(road_results)

            # â”€â”€ Corridor aggregate KPIs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            agg_cs      = np.mean([r["current_speed"]  for r in road_results])
            agg_ff      = np.mean([r["free_flow_speed"] for r in road_results])
            agg_cong    = np.mean([r["congestion_pct"]  for r in road_results])
            peak_delay  = max(r["delay_min"]            for r in road_results)
            any_closure = any(r["road_closure"]         for r in road_results)
            avg_conf    = np.mean([r["confidence"]      for r in road_results])
            agg_state, agg_color = classify_live_state(agg_cs, agg_ff, any_closure)

            # â”€â”€ Operational intelligence derivations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            most_impacted  = max(road_results, key=lambda r: r["congestion_pct"])
            highest_delay  = max(road_results, key=lambda r: r["delay_min"])
            worst_cong     = most_impacted
            pressure_idx   = get_corridor_pressure_index(agg_cong, peak_delay, n_live, n_total, any_closure)
            p_color        = get_pressure_color(pressure_idx)
            conf_tier, conf_color = get_confidence_tier(avg_conf, n_live, n_total)
            now_gst        = datetime.now().strftime("%H:%M")

            # â”€â”€ Live header (with timestamp + confidence) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            st.markdown(
                f"<div style='font-size:0.85rem; font-weight:700; color:#94A3B8; "
                f"letter-spacing:0.05em; text-transform:uppercase; margin-bottom:12px; "
                f"display:flex; align-items:center; gap:16px; flex-wrap:wrap;'>"
                f"<span>ðŸ“¡ Corridor Intelligence &nbsp;<span class='live-pulse'>LIVE</span></span>"
                f"<span style='font-size:0.66rem; color:#475569; font-weight:400; text-transform:none; letter-spacing:0;'>"
                f"{n_live}/{n_total} roads online</span>"
                f"<span style='font-size:0.66rem; color:{conf_color}; font-weight:600; text-transform:none; letter-spacing:0; "
                f"background:{conf_color}18; padding:2px 8px; border-radius:4px;'>{conf_tier}</span>"
                f"<span style='font-size:0.66rem; color:#475569; font-weight:400; text-transform:none; letter-spacing:0; margin-left:auto;'>"
                f"Last Updated: <strong style='color:#64748B;'>{now_gst} GST</strong></span>"
                f"</div>",
                unsafe_allow_html=True
            )

            # â”€â”€ Aggregate KPI row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            st.markdown("<div class='live-metric-row'>", unsafe_allow_html=True)
            lk1, lk2, lk3, lk4 = st.columns(4)
            lk1.metric("ðŸš¦ Corridor State", agg_state, f"Avg {agg_cs:.0f} km/h", delta_color="off")
            lk2.metric("ðŸ“Š Avg Congestion", f"{agg_cong:.0f}%", "network-wide avg", delta_color="inverse" if agg_cong > 20 else "normal")
            lk3.metric("â±ï¸ Peak Delay", f"{peak_delay:.1f} min", "worst single road", delta_color="inverse" if peak_delay > 1 else "normal")
            lk4.metric("ðŸ“Š Pressure Index", f"{pressure_idx} / 100", "calculated load", delta_color="off")
            st.markdown("</div>", unsafe_allow_html=True)

            # â”€â”€ Executive Intelligence Strip â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ei1, ei2, ei3 = st.columns(3)

            def _ei_card(col, icon, label, value, sub, vc="#E2E8F0"):
                col.markdown(
                    f"<div style='background:rgba(255,255,255,0.025); border:1px solid #1E293B; "
                    f"border-radius:10px; padding:12px 16px; margin-bottom:2px;'>"
                    f"<div style='font-size:0.62rem; font-weight:700; text-transform:uppercase; "
                    f"letter-spacing:0.08em; color:#64748B; margin-bottom:6px;'>{icon} {label}</div>"
                    f"<div style='font-size:1.05rem; font-weight:700; color:{vc}; margin-bottom:3px;'>{value}</div>"
                    f"<div style='font-size:0.68rem; color:#475569;'>{sub}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            _ei_card(ei1, "ðŸŸ¥", "Most Impacted Road",
                     most_impacted["road"],
                     f"{most_impacted['congestion_pct']:.0f}% congestion Â· {most_impacted['state']}",
                     vc=most_impacted["state_color"])
            _ei_card(ei2, "â³", "Highest Delay Road",
                     highest_delay["road"],
                     f"+{highest_delay['delay_min']:.1f} min above free-flow",
                     vc="#FFD600" if highest_delay["delay_min"] > 1 else "#00E5FF")
            _ei_card(ei3, "ðŸ“", "Worst Congestion Segment",
                     worst_cong["road"],
                     f"{worst_cong['current_speed']} km/h Â· free-flow {worst_cong['free_flow_speed']} km/h",
                     vc="#FF8F00" if worst_cong["congestion_pct"] > 35 else "#FFD600")

            # â”€â”€ Environmental context (above ranking) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if w_data:
                st.markdown(
                    f"<div class='weather-context'>"
                    f"<strong>Environmental Context <span class='live-badge'>LIVE</span> "
                    f"({weather_state} | {round(w_data['temperature_2m'])}Â°C):</strong> {weather_context}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            st.markdown("<div style='margin:14px 0 0;'></div>", unsafe_allow_html=True)

            # â”€â”€ Ranked roadway table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            sorted_roads = sorted(road_results, key=lambda r: r["congestion_pct"], reverse=True)

            def _cong_col(p):
                if p < 15: return "#00E5FF"
                if p < 35: return "#FFD600"
                if p < 60: return "#FF8F00"
                return "#FF006E"

            rows_html = ""
            for i, r in enumerate(sorted_roads, 1):
                cc  = _cong_col(r["congestion_pct"])
                tag = " ðŸš§" if r["road_closure"] else ""
                # Severity bar width
                bar_w = min(int(r["congestion_pct"]), 100)
                rows_html += (
                    f"<tr style='border-bottom:1px solid #0D1520;'>"
                    f"<td style='padding:9px 10px; color:#475569; font-size:0.74rem;'>{i}</td>"
                    # severity colour bar
                    f"<td style='padding:8px 6px; width:6px;'>"
                    f"<div style='width:4px; height:34px; border-radius:3px; background:{cc};'></div></td>"
                    f"<td style='padding:9px 12px; color:#E2E8F0; font-weight:600; white-space:nowrap;'>{r['road']}{tag}</td>"
                    f"<td style='padding:9px 12px; white-space:nowrap;'>"
                    f"<div style='display:flex; align-items:center; gap:7px;'>"
                    f"<div style='flex:1; height:5px; background:#0D1520; border-radius:3px; min-width:50px;'>"
                    f"<div style='width:{bar_w}%; height:100%; background:{cc}; border-radius:3px;'></div></div>"
                    f"<span style='color:{cc}; font-weight:700; font-size:0.79rem;'>{r['congestion_pct']:.0f}%</span>"
                    f"</div></td>"
                    f"<td style='padding:9px 12px; text-align:right; color:#F8FAFC; white-space:nowrap;'>"
                    f"{r['current_speed']} <span style='color:#475569; font-size:0.74rem;'>/ {r['free_flow_speed']} km/h</span></td>"
                    f"<td style='padding:9px 12px; text-align:right; color:#F8FAFC;'>"
                    f"{r['delay_min']:.1f} min</td>"
                    f"<td style='padding:9px 12px;'><span style='background:{r['state_color']}22; color:{r['state_color']}; "
                    f"padding:3px 8px; border-radius:4px; font-size:0.66rem; font-weight:700; white-space:nowrap;'>{r['state']}</span></td>"
                    f"</tr>"
                )

            st.markdown(
                f"""<div style='background:linear-gradient(145deg,#111827,#0F172A); border:1px solid #1F2937; border-radius:12px; overflow:hidden; margin-bottom:0;'>
<div style='padding:13px 18px; border-bottom:1px solid #1E293B;'>
  <span style='font-size:0.67rem; font-weight:700; text-transform:uppercase; letter-spacing:0.09em; color:#64748B;'>
    ðŸ“‹ Roadway Ranking â€” {selected_sector.upper()} &nbsp;Â·&nbsp; Sorted by congestion severity
  </span>
</div>
<div style='overflow-x:auto;'>
  <table style='width:100%; border-collapse:collapse; font-size:0.80rem; font-family:Inter,sans-serif;'>
    <thead>
      <tr style='border-bottom:1px solid #1E293B; color:#64748B; font-size:0.65rem; letter-spacing:0.07em; text-transform:uppercase;'>
        <th style='padding:10px 10px; text-align:left; font-weight:600;'>#</th>
        <th style='padding:10px 6px; width:6px;'></th>
        <th style='padding:10px 12px; text-align:left; font-weight:600;'>Roadway</th>
        <th style='padding:10px 12px; text-align:left; font-weight:600;'>Congestion</th>
        <th style='padding:10px 12px; text-align:right; font-weight:600;'>Speed</th>
        <th style='padding:10px 12px; text-align:right; font-weight:600;'>Delay</th>
        <th style='padding:10px 12px; text-align:left; font-weight:600;'>State</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
</div>""",
                unsafe_allow_html=True
            )

            # â”€â”€ Phase 2: Operational Deviation Intelligence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            baseline = get_baseline_comparison(df, selected_region, target_h, agg_cs, agg_ff)
            if baseline:
                vp         = baseline["variance_pct"]
                vp_sign    = "+" if vp >= 0 else ""
                dev_col    = baseline["dev_color"]
                exp_spd    = baseline["expected_speed"]
                hist_delay = baseline["hist_delay"]
                st.markdown(
                    f"""<div style='margin-top:12px; background:linear-gradient(145deg,#0C1526,#0A1120);
                    border:1px solid #1E293B; border-radius:12px; padding:0; overflow:hidden;'>
  <div style='padding:12px 18px; border-bottom:1px solid #1E293B; display:flex; align-items:center; gap:10px;'>
    <span style='font-size:0.67rem; font-weight:700; text-transform:uppercase; letter-spacing:0.09em; color:#64748B;'>
      âš¡ Operational Deviation Intelligence
    </span>
    <span style='margin-left:auto; font-size:0.63rem; color:#475569;'>
      vs {baseline['city']} historical baseline Â· {target_h:02d}:00 GST Â· {baseline['n_samples']} datapoints
    </span>
  </div>
  <div style='display:grid; grid-template-columns:1fr 1fr 1fr 1.4fr; padding:16px 18px; gap:24px;'>
    <div>
      <div style='font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; margin-bottom:5px;'>Live Avg Speed</div>
      <div style='font-size:1.25rem; font-weight:700; color:#F8FAFC;'>{agg_cs:.0f} <span style='font-size:0.75rem; color:#64748B;'>km/h</span></div>
      <div style='font-size:0.67rem; color:#475569;'>Free-flow: {agg_ff:.0f} km/h</div>
    </div>
    <div>
      <div style='font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; margin-bottom:5px;'>Expected Baseline</div>
      <div style='font-size:1.25rem; font-weight:700; color:#94A3B8;'>{exp_spd} <span style='font-size:0.75rem; color:#64748B;'>km/h</span></div>
      <div style='font-size:0.67rem; color:#475569;'>Hist. inflation: +{baseline['expected_infl']:.1f}%</div>
    </div>
    <div>
      <div style='font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; margin-bottom:5px;'>Operational Variance</div>
      <div style='font-size:1.25rem; font-weight:700; color:{dev_col};'>{vp_sign}{vp:.1f}%</div>
      <div style='font-size:0.67rem; color:#475569;'>speed ratio deviation</div>
    </div>
    <div style='border-left:1px solid #1E293B; padding-left:20px;'>
      <div style='font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; margin-bottom:5px;'>Interpretation</div>
      <div style='font-size:0.88rem; font-weight:700; color:{dev_col}; margin-bottom:4px;'>{baseline['dev_label']}</div>
      <div style='font-size:0.67rem; color:#475569;'>Hist. avg delay: {hist_delay:.1f} min</div>
    </div>
  </div>
</div>""",
                    unsafe_allow_html=True
                )

            st.markdown("<div style='margin:14px 0 0;'></div>", unsafe_allow_html=True)

            # â”€â”€ Corridor map â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            fig_live   = go.Figure()
            # Intelligent map focus: center on most congested road, not geometric mean
            focus_road  = most_impacted
            center_lat  = focus_road["lat"]
            center_lon  = focus_road["lon"]

            # Road geometry lines (where TomTom returns segment coords)
            for r in road_results:
                if r["geo_coords"]:
                    fig_live.add_trace(go.Scattermapbox(
                        lat=[c["latitude"]  for c in r["geo_coords"]],
                        lon=[c["longitude"] for c in r["geo_coords"]],
                        mode="lines",
                        line=dict(width=5, color=r["state_color"]),
                        hoverinfo="skip",
                        showlegend=False
                    ))

            # Road markers â€” color = operational state
            fig_live.add_trace(go.Scattermapbox(
                lat=[r["lat"] for r in road_results],
                lon=[r["lon"] for r in road_results],
                mode="markers",
                marker=dict(
                    size=18,
                    color=[r["state_color"] for r in road_results]
                ),
                text=[r["road"] for r in road_results],
                customdata=[
                    [r["current_speed"], r["free_flow_speed"],
                     f"{r['congestion_pct']:.0f}", r["state"], f"{r['delay_min']:.1f}"]
                    for r in road_results
                ],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "%{customdata[3]}<br>"
                    "Speed: %{customdata[0]} / %{customdata[1]} km/h<br>"
                    "Congestion: %{customdata[2]}%  |  Delay: +%{customdata[4]} min"
                    "<extra></extra>"
                ),
                showlegend=False
            ))

            # Auto-zoom based on corridor geographic spread
            lat_spread = max(r["lat"] for r in road_results) - min(r["lat"] for r in road_results)
            lon_spread = max(r["lon"] for r in road_results) - min(r["lon"] for r in road_results)
            spread     = max(lat_spread, lon_spread)
            auto_zoom  = 12 if spread > 0.08 else 13 if spread > 0.04 else 14 if spread > 0.015 else 15

            # â”€â”€ TomTom traffic flow tile layer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # relative0-dark: dark-optimised, green=free-flow â†’ red=gridlock
            tile_url = (
                f"https://api.tomtom.com/traffic/map/4/tile/flow/"
                f"relative0-dark/{{z}}/{{x}}/{{y}}.png?key={_live_key}"
            )
            mapbox_layers = [{
                "below":           "traces",
                "sourcetype":      "raster",
                "source":          [tile_url],
                "opacity":         0.82,
                "sourceattribution": "TomTom Traffic Flow",
            }]

            fig_live.update_layout(
                mapbox=dict(
                    style="carto-darkmatter",
                    center=dict(lat=center_lat, lon=center_lon),
                    zoom=auto_zoom,
                    layers=mapbox_layers,
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=0, b=0),
                height=520,
                showlegend=False,
                hoverlabel=dict(bgcolor="#161F2E", bordercolor="#FF006E", font_size=13)
            )

            # â”€â”€ Map header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            st.markdown(
                f"<div style='font-size:0.67rem; font-weight:700; text-transform:uppercase; "
                f"letter-spacing:0.09em; color:#64748B; margin-bottom:6px;'>"
                f"ðŸ—ºï¸ Live Traffic Flow Map â€” {selected_sector}, {selected_region} "
                f"&nbsp;<span style='color:#FF006E; font-size:0.62rem;'>TomTom Flow Tiles ACTIVE</span></div>",
                unsafe_allow_html=True
            )

            st.plotly_chart(fig_live, width='stretch', config={"displayModeBar": False})

            # â”€â”€ Traffic flow legend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            st.markdown(
                "<div style='display:flex; align-items:center; gap:20px; "
                "padding:8px 14px; background:rgba(255,255,255,0.03); "
                "border:1px solid #1E293B; border-radius:8px; margin-top:6px; "
                "font-size:0.70rem; color:#94A3B8;'>"
                "<span style='font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#64748B; margin-right:4px;'>Traffic Flow:</span>"
                "<span><span style='display:inline-block; width:12px; height:12px; border-radius:50%; background:#1DB954; margin-right:5px; vertical-align:middle;'></span>Smooth</span>"
                "<span><span style='display:inline-block; width:12px; height:12px; border-radius:50%; background:#FFA500; margin-right:5px; vertical-align:middle;'></span>Moderate</span>"
                "<span><span style='display:inline-block; width:12px; height:12px; border-radius:50%; background:#FF4500; margin-right:5px; vertical-align:middle;'></span>Congested</span>"
                "<span><span style='display:inline-block; width:12px; height:12px; border-radius:50%; background:#8B0000; margin-right:5px; vertical-align:middle;'></span>Severe</span>"
                "<span style='margin-left:auto; font-size:0.63rem; color:#475569;'>Source: TomTom Traffic Flow Tiles Â· Pins = monitored road segments</span>"
                "</div>",
                unsafe_allow_html=True
            )

    st.caption(
        f"ðŸ›°ï¸ Live Corridor Telemetry â€” {selected_sector}, {selected_region}  "
        f"| TomTom Traffic Flow API  "
        f"| Auto-refreshes every 120 seconds"
    )


# =========================================================
# 10. HISTORICAL INTELLIGENCE (shown when live = OFF)
#     Includes: Diagnosis, Forecast / Simulation, Posture Map
# =========================================================
elif live_enabled and not selected_sector:
    st.markdown("---")
    st.info("Select a corridor from the sidebar to load live roadway telemetry.")

else:
    # â”€â”€ Simulation mode suspension notice â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if live_enabled and selected_severity != "Observed Conditions":
        st.markdown("---")
        st.markdown(
            "<div style='background:rgba(124,58,237,0.08); border-left:3px solid #7C3AED; "
            "padding:12px 18px; border-radius:0 8px 8px 0; font-size:0.84rem; color:#94A3B8;'>"
            "ðŸ”’ <strong style='color:#CBD5E1;'>Live telemetry suspended during simulation mode.</strong> "
            "Simulations are synthetic operational stress models â€” mixing them with live roadway data "
            "would compromise analytical integrity. Return to <em>Observed Conditions</em> to enable live telemetry."
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # â”€â”€ Operational Diagnosis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    col_diag, col_empty = st.columns([2, 1])
    with col_diag:
        st.markdown("### ðŸ§  Operational Diagnosis")
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

        if w_data:
            st.markdown(
                f"<div class='weather-context'>"
                f"<strong>Current Environmental Conditions <span class='live-badge'>LIVE</span> "
                f"({weather_state} | {round(w_data['temperature_2m'])}Â°C):</strong> {weather_context}"
                f"</div>",
                unsafe_allow_html=True
            )

    # â”€â”€ Forecast / Simulation Chart â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hours_to_plot      = [(target_h - 2) % 24, (target_h - 1) % 24, target_h, (target_h + 1) % 24, (target_h + 2) % 24]
    baseline_trajectory = []
    sim_trajectory      = []

    for h in hours_to_plot:
        h_df = df[(df['City_UI'] == selected_city) & (df['Hour'] == h)]
        if len(h_df) > 0:
            b_f   = max(h_df['TrafficFrictionScore'].mean(), 0)
            b_d   = max(h_df['TravelDelayMinutes'].mean(), 0)
            b_j   = max(h_df['JamLengthKm'].mean(), 0)
            b_sev = b_f + (b_d * 4) + (b_j / 120)
            baseline_trajectory.append({'Hour': f"{h:02d}:00", 'ForecastSeverity': b_sev, 'Trajectory': 'Observed Baseline'})

            if selected_severity != "Observed Conditions":
                if hours_to_plot.index(h) >= 2:
                    s_f = b_f * mult['f']; s_d = b_d * mult['d']; s_j = b_j * mult['j']
                    if h in [0, 1, 2, 3, 4]:   s_f *= 0.65; s_j *= 0.6; s_d *= 0.5
                    if h in [5, 6]:             s_f *= 0.8;  s_j *= 0.8; s_d *= 0.8
                    if h in [16, 17, 18, 19]:   s_f *= 1.2;  s_j *= 1.25; s_d *= 1.3
                    s_sev = max(s_f, 0) + (max(s_d, 0) * 4) + (max(s_j, 0) / 120)
                    sim_trajectory.append({'Hour': f"{h:02d}:00", 'ForecastSeverity': s_sev, 'Trajectory': f'{selected_severity} Simulation'})
                else:
                    sim_trajectory.append({'Hour': f"{h:02d}:00", 'ForecastSeverity': b_sev, 'Trajectory': f'{selected_severity} Simulation'})

    if selected_severity != "Observed Conditions":
        st.markdown("<br>### âš–ï¸ Operational Scenario Comparison", unsafe_allow_html=True)
        st.markdown("<div class='sim-warning'>Scenario values computationally amplified for operational comparison. Forecasting is disabled during simulation mode to preserve analytical realism.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<br>### ðŸ”® Next 4-Hour Mobility Forecast", unsafe_allow_html=True)
        st.caption("Based on observed historical mobility behavior")

    combined_df = pd.DataFrame(baseline_trajectory + sim_trajectory) if selected_severity != "Observed Conditions" else pd.DataFrame(baseline_trajectory)
    fig = px.line(combined_df, x="Hour", y="ForecastSeverity", color="Trajectory", markers=True,
                  color_discrete_sequence=['#00E5FF', '#FF006E'] if selected_severity != "Observed Conditions" else ['#00E5FF'])

    if selected_severity != "Observed Conditions":
        fig.update_traces(line=dict(dash="dot"), selector=dict(name="Observed Baseline"))

    current_hour_str = f"{target_h:02d}:00"
    fig.add_vline(x=current_hour_str, line_width=1, line_dash="dash", line_color="white", opacity=0.5)
    fig.add_annotation(x=current_hour_str, y=1, yref="paper", text="Active Hour",
                       showarrow=False, font=dict(color="white", size=10), yshift=15)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'), yaxis_title="Severity Index", xaxis_title="",
        legend=dict(orientation="h", y=1.1, x=1),
        margin=dict(t=30, b=0, l=0, r=0), height=400
    )
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

    # â”€â”€ National Operational Posture Map â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("---")
    st.markdown("## ðŸ—ºï¸ National Operational Posture")

    m_df = df[df['Hour'] == target_h].groupby('City_UI')[
        ['TrafficFrictionScore', 'TravelTimeInflationPct', 'JamLengthKm', 'TravelDelayMinutes', 'NetworkShockEscalation']
    ].mean().reset_index()

    m_df['TrafficFrictionScore']    *= mult['f']
    m_df['TravelTimeInflationPct']  *= mult['p']
    m_df['TravelDelayMinutes']      *= mult['d']
    m_df['JamLengthKm']             *= mult['j']
    m_df['NetworkShockEscalation']  *= mult['r']

    if target_h in [0, 1, 2, 3, 4]:   m_df['TrafficFrictionScore'] *= 0.65; m_df['TravelDelayMinutes'] *= 0.5
    if target_h in [5, 6]:             m_df['TrafficFrictionScore'] *= 0.8;  m_df['TravelDelayMinutes'] *= 0.8
    if target_h in [16, 17, 18, 19]:   m_df['TrafficFrictionScore'] *= 1.2;  m_df['TravelDelayMinutes'] *= 1.3

    m_df['lat'] = m_df['City_UI'].map(lambda x: CITY_COORDS.get(x, {}).get('lat', 0))
    m_df['lon'] = m_df['City_UI'].map(lambda x: CITY_COORDS.get(x, {}).get('lon', 0))

    m_df['CityHourBaseline'] = m_df['City_UI'].apply(
        lambda c: max(df[(df['City_UI'] == c) & (df['Hour'] == target_h)]['TrafficFrictionScore'].mean(), 0.5))
    m_df['OperationalSeverity'] = (
        ((m_df['TrafficFrictionScore'].clip(lower=0) / m_df['CityHourBaseline']) * 15) +
        (m_df['TravelTimeInflationPct'].abs() * 2) +
        (m_df['TravelDelayMinutes'].clip(lower=0) * 8)
    )
    s_min, s_max = m_df['OperationalSeverity'].min(), m_df['OperationalSeverity'].max()
    m_df['BubbleSize'] = ((m_df['OperationalSeverity'] - s_min) / ((s_max - s_min) + 0.01) * 55) + 10
    m_df['Narrative']  = m_df.apply(
        lambda row: get_typology_diagnosis(row['TrafficFrictionScore'], row['TravelDelayMinutes'], row['JamLengthKm']),
        axis=1
    )

    fig_map = px.scatter_mapbox(
        m_df, lat='lat', lon='lon', size='BubbleSize', color='OperationalSeverity',
        hover_name='City_UI',
        hover_data={'lat': False, 'lon': False, 'OperationalSeverity': False, 'BubbleSize': False, 'Narrative': True},
        color_continuous_scale=m_cols, zoom=6.2
    )
    fig_map.update_traces(hovertemplate="<b style='font-size:16px'>%{hovertext}</b><br><br><b>State:</b> %{customdata[0]}<extra></extra>")
    fig_map.update_layout(
        mapbox_style=m_style, paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'), height=550,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor="#161F2E", bordercolor="#FF006E", font_size=14)
    )
    st.plotly_chart(fig_map, width='stretch', config={'displayModeBar': False})
    st.caption(
        "UAE Mobility Intelligence Console â€¢ Baseline Reality Edition"
        if selected_severity == "Observed Conditions"
        else "UAE Mobility Intelligence Console â€¢ Simulation Engine Active"
    )
