import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import io
import re
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================
GITHUB_REPO = "AayuGo1/Environment_Health_-_Safety"
GITHUB_BRANCH = "main"
EXCEL_FILENAME = "Monthly KPI Summary Sheet_April_GNSC.xlsx"
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{EXCEL_FILENAME}"

COLORS = {
    "bg_primary": "#0B132B", "bg_secondary": "#1C2541", "card_bg": "#FFFFFF",
    "text_light": "#FFFFFF", "text_dark": "#1A202C", "green": "#38A169",
    "orange": "#DD6B20", "red": "#E53E3E", "blue": "#3182CE", "teal": "#319795",
}

MONTH_PATTERN = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$'

# ==============================================================================
# PAGE SETUP & STYLING
# ==============================================================================
st.set_page_config(page_title="EHS Dashboard | GNSC", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

def inject_custom_css():
    st.markdown(f"""
        <style>
            .stApp {{ background-color: {COLORS['bg_primary']}; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; 
                      background-color: {COLORS['bg_secondary']}; border-radius: 0 0 16px 16px; margin-bottom: 2rem; border-bottom: 1px solid #2D3748; }}
            .title {{ color: {COLORS['text_light']}; font-size: 1.8rem; font-weight: 700; }}
            .subtitle {{ color: #A0AEC0; font-size: 0.9rem; }}
            div[data-testid="stMetric"] {{ background-color: {COLORS['card_bg']}; padding: 20px; border-radius: 12px; 
                                          box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 1px solid #E2E8F0; }}
            [data-testid="stMetricLabel"] > label {{ color: {COLORS['text_dark']} !important; font-weight: 600; }}
            [data-testid="stMetricValue"] {{ color: {COLORS['text_dark']} !important; font-size: 2.2rem !important; font-weight: 700; }}
            section[data-testid="stSidebar"] {{ background-color: {COLORS['bg_secondary']}; border-right: 1px solid #2D3748; }}
            .stSelectbox label, .stMultiSelect label, .stCheckbox label {{ color: {COLORS['text_light']} !important; }}
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# DATA LOADING ENGINE (FIXED)
# ==============================================================================
@st.cache_data(ttl=3600)
def load_data_from_github():
    try:
        resp = requests.get(RAW_URL, timeout=30)
        resp.raise_for_status()
        xls = pd.ExcelFile(io.BytesIO(resp.content))
        
        # Parse Environment Sheet with Multi-Level Headers
        env_df = pd.read_excel(xls, sheet_name="Environment", header=[0, 1, 2])
        
        # Flatten columns: "Category | Subcategory | KPI Name"
        flat_cols = []
        for col in env_df.columns:
            parts = [str(c).strip() for c in col if str(c).strip() not in ('nan', 'None', '')]
            flat_cols.append(" | ".join(parts) if parts else "Unnamed")
        env_df.columns = flat_cols
        
        # Dynamically detect month columns
        month_cols = [c for c in env_df.columns if re.search(MONTH_PATTERN, c.split('|')[-1].strip(), re.IGNORECASE)]
        
        # Parse H&S Sheet
        hs_df = pd.DataFrame()
        if "H&S" in xls.sheet_names:
            hs_df = pd.read_excel(xls, sheet_name="H&S", header=[0, 1, 2])
            hs_flat = []
            for col in hs_df.columns:
                parts = [str(c).strip() for c in col if str(c).strip() not in ('nan', 'None', '')]
                hs_flat.append(" | ".join(parts) if parts else "Unnamed")
            hs_df.columns = hs_flat

        return {
            "environment": {"df": env_df, "month_cols": month_cols},
            "health_safety": {"df": hs_df},
            "last_updated": datetime.now().strftime("%d-%b-%y %H:%M")
        }
    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
        return None

# ==============================================================================
# ANALYTICS & UI HELPERS
# ==============================================================================
def get_kpi_value(df, search_term):
    matches = [c for c in df.columns if search_term.lower() in c.lower()]
    if not matches: return None
    val = df.iloc[0][matches[0]]
    if isinstance(val, str) and '%' in val: return float(val.replace('%', ''))
    try: return float(val)
    except: return None

def calculate_status(actual, target, lower_is_better=False):
    if actual is None or target is None or pd.isna(target) or target == 0:
        return None, None, "ℹ️ No Target"
    if lower_is_better:
        ach = (target / actual * 100) if actual > 0 else 100
        status = "✅ On Track" if actual <= target else "⚠️ Off Track"
    else:
        ach = (actual / target * 100) if target > 0 else 0
        status = "✅ On Track" if actual >= target else "⚠️ Off Track"
    return round(ach, 1), round(abs(actual - target), 2), status

def render_kpi_card(title, value, unit, target, achievement, status):
    delta_text = f"{achievement}% of Target" if achievement else None
    st.metric(label=title, value=f"{value:,.2f} {unit}" if value is not None else "N/A", 
              delta=delta_text, delta_color="inverse" if "On Track" in str(status) else "normal",
              help=f"Target: {target} | Status: {status}")

def render_trend_chart(df, x_col, y_cols, title):
    fig = px.line(df, x=x_col, y=y_cols, title=title, markers=True, template="plotly_white", height=400)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# MAIN DASHBOARD LAYOUT
# ==============================================================================
st.markdown(f"""
    <div class="header">
        <div><div class="title">🛡️ EHS DASHBOARD</div><div class="subtitle">Health, Safety & Environment | GNSC Plant</div></div>
        <div style="color:{COLORS['text_light']}; text-align:right; font-weight:bold;">Data as on<br><span style="color:#A0AEC0; font-weight:normal;">Loading...</span></div>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🔍 Filters")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.selectbox("Financial Year", ["2025-2026"], index=0)
    st.divider()
    show_energy = st.checkbox("Energy", value=True)
    show_water = st.checkbox("Water", value=True)
    show_waste = st.checkbox("Waste", value=True)
    show_hs = st.checkbox("Health & Safety", value=True)

# LOAD DATA
data = load_data_from_github()
if data is None: st.stop()

env_info = data["environment"]
env_df = env_info["df"]
month_cols = env_info["month_cols"]

# Update timestamp
st.components.v1.html(f"""<script>document.querySelector('.header div:last-child span').innerText = "{data['last_updated']}";</script>""", height=0)

# --- EXECUTIVE SUMMARY ---
st.subheader(" Executive Summary")
exec_kpis = [
    ("Energy Intensity", "Total energy consumption [kWh/Gross Weight (t Metric)]", "kWh/MT", True),
    ("Water Intensity", "Total water withdrawal  [m³/Gross Weight (t Metric)]", "m³/MT", True),
    ("Waste Intensity", "Total waste per t(Metrics) [kg/Gross Weight (t Metric)]", "kg/MT", True),
    ("Production Volume", "Production Volume - Gross Weight [Gross Weight (t Metric)]", "MT", False),
]

cols = st.columns(len(exec_kpis))
for i, (name, search, unit, low_better) in enumerate(cols):
    current = get_kpi_value(env_df, search)
    target = get_kpi_value(env_df, search.replace('[','').replace(']',''))
    ach, _, status = calculate_status(current, target, low_better)
    with cols[i]: render_kpi_card(name, current, unit, target, ach, status)

# --- MONTHLY TRENDS ---
st.subheader("📈 Monthly Performance Trends")
trend_rows = [{"Month": mc, **{col: env_df.iloc[0][col] for col in env_df.columns if mc in col}} for mc in month_cols]
trend_df = pd.DataFrame(trend_rows)

tab1, tab2, tab3 = st.tabs(["⚡ Energy", " Water", "♻️ Waste"])
with tab1:
    c = next((c for c in env_df.columns if "Total energy consumption [kWh/Gross" in c), None)
    if c: render_trend_chart(trend_df, "Month", [c], "Energy Intensity Trend (kWh/MT)")
with tab2:
    c = next((c for c in env_df.columns if "Total water withdrawal  [m³/Gross" in c), None)
    if c: render_trend_chart(trend_df, "Month", [c], "Water Intensity Trend (m³/MT)")
with tab3:
    c = next((c for c in env_df.columns if "Total waste per t(Metrics)" in c), None)
    if c: render_trend_chart(trend_df, "Month", [c], "Waste Intensity Trend (kg/MT)")

# --- WASTE COMPOSITION ---
st.subheader("♻️ Waste Composition Analysis")
col_w1, col_w2 = st.columns([2, 1])
with col_w1:
    c = next((c for c in env_df.columns if "Total waste [kg]" in c), None)
    if c: render_trend_chart(trend_df, "Month", [c], "Total Waste Generation (kg)")
with col_w2:
    latest = month_cols[-1] if month_cols else None
    if latest:
        cats = [c for c in env_df.columns if ("recycled" in c.lower() or "landfill" in c.lower()) and latest in c]
        if cats:
            comp = pd.DataFrame({"Category": [c.split("|")[-1][:25] for c in cats], "Value": [env_df.iloc[0][c] for c in cats]})
            fig = px.pie(comp, values="Value", names="Category", hole=0.6, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

# --- H&S SUMMARY ---
if show_hs and not data["health_safety"]["df"].empty:
    st.subheader("🦺 Health & Safety KPI Summary")
    hs_df = data["health_safety"]["df"]
    kpis = ["Fatalities", "Lost Time Injury", "First Aid Accident", "Near miss", "% of UA/UC Closure"]
    rows = []
    for k in kpis:
        cur = get_kpi_value(hs_df, k)
        tgt = get_kpi_value(hs_df, k)
        low = any(x in k.lower() for x in ["fatality", "injury", "accident"])
        ach, _, stat = calculate_status(cur, tgt, low)
        rows.append({"KPI": k[:40], "Actual": cur, "Target": tgt, "Achievement %": ach, "Status": stat})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(f"Last Refresh: {data['last_updated']} | Source: GitHub | Built with Streamlit & Plotly")
