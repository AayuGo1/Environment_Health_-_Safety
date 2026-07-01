import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
import re
from datetime import datetime
GITHUB_REPO = "AayuGo1/Environment_Health_-_Safety"  
GITHUB_BRANCH = "main"                              
EXCEL_FILENAME = "Monthly KPI Summary Sheet_April_GNSC.xlsx"  
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{EXCEL_FILENAME}"

# Enterprise Color Palette
COLORS = {
    "bg_primary": "#0B132B",
    "bg_secondary": "#1C2541",
    "card_bg": "#FFFFFF",
    "text_light": "#FFFFFF",
    "text_dark": "#1A202C",
    "green": "#38A169",
    "orange": "#DD6B20",
    "red": "#E53E3E",
    "blue": "#3182CE",
    "teal": "#319795",
}

# Month pattern for dynamic detection
MONTH_PATTERN = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$'

# ==============================================================================
# PAGE SETUP & STYLING
# ==============================================================================
st.set_page_config(
    page_title="EHS Dashboard | GNSC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    """Injects premium enterprise styling"""
    st.markdown(f"""
        <style>
            .stApp {{ background-color: {COLORS['bg_primary']}; }}
            
            /* Header */
            .header {{
                display: flex; justify-content: space-between; align-items: center;
                padding: 1rem 2rem; background-color: {COLORS['bg_secondary']};
                border-radius: 0 0 16px 16px; margin-bottom: 2rem;
                border-bottom: 1px solid #2D3748;
            }}
            .title {{ color: {COLORS['text_light']}; font-size: 1.8rem; font-weight: 700; }}
            .subtitle {{ color: #A0AEC0; font-size: 0.9rem; }}
            .timestamp {{ color: {COLORS['text_light']}; text-align: right; font-weight: bold; }}
            
            /* Cards */
            div[data-testid="stMetric"] {{
                background-color: {COLORS['card_bg']}; padding: 20px;
                border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                border: 1px solid #E2E8F0;
            }}
            [data-testid="stMetricLabel"] > label {{ color: {COLORS['text_dark']} !important; font-weight: 600; font-size: 0.9rem; }}
            [data-testid="stMetricValue"] {{ color: {COLORS['text_dark']} !important; font-size: 2.2rem !important; font-weight: 700; }}
            [data-testid="stMetricDelta"] {{ color: {COLORS['text_dark']} !important; font-size: 0.9rem; }}
            
            /* Sidebar */
            section[data-testid="stSidebar"] {{ background-color: {COLORS['bg_secondary']}; border-right: 1px solid #2D3748; }}
            .stSelectbox label, .stMultiSelect label, .stCheckbox label {{ color: {COLORS['text_light']} !important; }}
            
            /* Charts */
            .chart-container {{
                background-color: {COLORS['card_bg']}; padding: 20px;
                border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-bottom: 20px;
            }}
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

@st.cache_data(ttl=3600)
def load_data_from_github():
    try:
        st.write("🔄 Fetching data from GitHub...")
        resp = requests.get(RAW_URL, timeout=30)
        resp.raise_for_status()
        
        st.write("✅ File downloaded. Parsing Excel...")
        xls = pd.ExcelFile(io.BytesIO(resp.content))
        
        # Parse Environment Sheet
        env_df = pd.read_excel(xls, sheet_name="Environment", header=[0, 1, 2])
        st.write(f"📊 Environment sheet loaded: {env_df.shape}")
        
        # Flatten columns safely
        flat_cols = []
        for col in env_df.columns:
            parts = [str(c).strip() for c in col if str(c).strip() not in ('nan', 'None', '')]
            flat_cols.append(" | ".join(parts) if parts else "Unnamed")
        env_df.columns = flat_cols
        
        # Identify month columns dynamically
        month_pattern = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$'
        month_cols = [c for c in env_df.columns if re.search(month_pattern, c.split('|')[-1].strip(), re.IGNORECASE)]
        st.write(f"📅 Detected {len(month_cols)} month columns: {month_cols[:3]}...")
        
        return {"environment": env_df, "month_cols": month_cols}, datetime.now().strftime("%d-%b-%y")
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ GitHub Connection Failed: {e}")
        st.info("Check if repo is public or if GITHUB_TOKEN is set in Secrets.")
        return None, None
    except Exception as e:
        st.error(f"❌ Data Parsing Error: {e}")
        st.exception(e)  # Shows full traceback in browser
        return None, None

# ==============================================================================
# ANALYTICS ENGINE
# ==============================================================================
def get_kpi_value(df, kpi_partial_name, col_type="current"):
    """Safely extract KPI values using partial name matching."""
    matches = [c for c in df.columns if kpi_partial_name.lower() in c.lower()]
    if not matches:
        return None
    
    col = matches[0]
    val = df.iloc[0][col]
    
    # Handle percentage strings
    if isinstance(val, str) and '%' in val:
        return float(val.replace('%', ''))
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def calculate_status(actual, target, lower_is_better=False):
    """Calculate achievement % and traffic light status."""
    if actual is None or target is None or pd.isna(target) or target == 0:
        return None, None, "ℹ️ No Target"
    
    if lower_is_better:
        achievement = (target / actual * 100) if actual > 0 else 100
        status = "✅ On Track" if actual <= target else "⚠️ Off Track"
    else:
        achievement = (actual / target * 100) if target > 0 else 0
        status = "✅ On Track" if actual >= target else "⚠️ Off Track"
    
    return round(achievement, 1), round(abs(actual - target), 2), status

# ==============================================================================
# UI COMPONENTS
# ==============================================================================
def render_kpi_card(title, value, unit, target, achievement, status, sparkline=None):
    """Renders an enterprise KPI card with optional sparkline."""
    delta_text = None
    delta_color = "normal"
    
    if achievement is not None:
        delta_text = f"{achievement}% of Target"
        if "On Track" in status:
            delta_color = "inverse"
        elif "Off Track" in status:
            delta_color = "inverse"
    
    st.metric(
        label=title,
        value=f"{value:,.2f} {unit}" if value is not None else "N/A",
        delta=delta_text,
        delta_color=delta_color,
        help=f"Target: {target} | Status: {status}"
    )
    
    if sparkline is not None and len(sparkline) > 0:
        fig = px.line(y=sparkline, template="plotly_white", height=50)
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False, xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False, showgrid=False)
        )
        fig.update_traces(line=dict(color=COLORS['blue'], width=2))
        st.plotly_chart(fig, use_container_width=True)

def render_trend_chart(df, x_col, y_cols, title, y_title="Value", height=400):
    """Professional multi-line trend chart."""
    fig = px.line(df, x=x_col, y=y_cols, title=title, markers=True, 
                  template="plotly_white", height=height)
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(240,242,245,0.5)', hovermode="x unified",
        yaxis_title=y_title
    )
    st.plotly_chart(fig, use_container_width=True)

def render_donut(df, values, names, title):
    """Composition donut chart."""
    fig = px.pie(df, values=values, names=names, title=title, hole=0.6, 
                 template="plotly_white", height=350)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05))
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# MAIN DASHBOARD LAYOUT
# ==============================================================================
# HEADER
st.markdown(f"""
    <div class="header">
        <div>
            <div class="title">🛡️ EHS DASHBOARD</div>
            <div class="subtitle">Health, Safety & Environment | GNSC Plant</div>
        </div>
        <div class="timestamp" id="last-updated">Loading...</div>
    </div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("🔍 Filters")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    fy = st.selectbox("Financial Year", ["2025-2026"], index=0)
    month_filter = st.selectbox("Month", ["All"] + [m.split('|')[-1].strip() for m in 
                              (load_data_from_github()[0].get("Environment", {}).get("month_cols", []) 
                               if load_data_from_github()[0] else [])])
    
    st.divider()
    st.caption("KPI Categories")
    show_energy = st.checkbox("Energy", value=True)
    show_water = st.checkbox("Water", value=True)
    show_waste = st.checkbox("Waste", value=True)
    show_hs = st.checkbox("Health & Safety", value=True)

# LOAD DATA
data, last_updated = load_data_from_github()
if data is None:
    st.stop()

# Update timestamp in header via JS workaround
st.components.v1.html(f"""
    <script>
        document.getElementById('last-updated').innerHTML = 
            '<div style="color:{COLORS["text_light"]};font-weight:bold;">Data as on</div>' +
            '<div style="color:#A0AEC0;">{last_updated}</div>';
    </script>
""", height=0)

env_data = data.get("Environment", {})
hs_data = data.get("H&S", {})
env_df = env_data.get("df", pd.DataFrame())
hs_df = hs_data.get("df", pd.DataFrame())
month_cols = env_data.get("month_cols", [])

# --- EXECUTIVE SUMMARY ---
st.subheader("📊 Executive Summary")

exec_kpis = [
    ("Energy Intensity", "Total energy consumption [kWh/Gross Weight (t Metric)]", "kWh/MT", True),
    ("Water Intensity", "Total water withdrawal  [m³/Gross Weight (t Metric)]", "m³/MT", True),
    ("Waste Intensity", "Total waste per t(Metrics) [kg/Gross Weight (t Metric)]", "kg/MT", True),
    ("Production Volume", "Production Volume - Gross Weight [Gross Weight (t Metric)]", "MT", False),
]

cols = st.columns(len(exec_kpis))
for i, (name, search_term, unit, lower_better) in enumerate(cols):
    current = get_kpi_value(env_df, search_term)
    target = get_kpi_value(env_df, search_term.replace('[', '').replace(']', ''))  # Fallback
    
    # Get sparkline (last 3 months)
    spark = [get_kpi_value(env_df, search_term)]  # Simplified; ideally extract from month cols
    
    ach, var, status = calculate_status(current, target, lower_better)
    
    with cols[i]:
        render_kpi_card(name, current, unit, target, ach, status, sparkline=spark)

# --- MONTHLY TRENDS ---
st.subheader("📈 Monthly Performance Trends")

# Prepare transposed trend data
trend_rows = []
for mc in month_cols:
    row = {"Month": mc}
    for col in env_df.columns:
        if mc in col or col == mc:
            row[col] = env_df.iloc[0][col]
    trend_rows.append(row)
trend_df = pd.DataFrame(trend_rows)

tab1, tab2, tab3 = st.tabs(["⚡ Energy", "💧 Water", "♻️ Waste"])

with tab1:
    energy_col = next((c for c in env_df.columns if "Total energy consumption [kWh/Gross" in c), None)
    if energy_col:
        render_trend_chart(trend_df, "Month", [energy_col], "Energy Intensity Trend (kWh/MT)")

with tab2:
    water_col = next((c for c in env_df.columns if "Total water withdrawal  [m³/Gross" in c), None)
    if water_col:
        render_trend_chart(trend_df, "Month", [water_col], "Water Intensity Trend (m³/MT)")

with tab3:
    waste_col = next((c for c in env_df.columns if "Total waste per t(Metrics)" in c), None)
    if waste_col:
        render_trend_chart(trend_df, "Month", [waste_col], "Waste Intensity Trend (kg/MT)")

# --- WASTE COMPOSITION ---
st.subheader("♻️ Waste Composition Analysis")
col_w1, col_w2 = st.columns([2, 1])

with col_w1:
    total_waste_col = next((c for c in env_df.columns if "Total waste [kg]" in c), None)
    if total_waste_col:
        render_trend_chart(trend_df, "Month", [total_waste_col], "Total Waste Generation (kg)")

with col_w2:
    # Build composition from latest month
    latest = month_cols[-1] if month_cols else None
    if latest:
        waste_cats = [c for c in env_df.columns if ("recycled" in c.lower() or "landfill" in c.lower() or 
                      "incineration" in c.lower()) and latest in c]
        comp_data = pd.DataFrame({
            "Category": [c.split("|")[-1].strip()[:25] for c in waste_cats],
            "Value": [env_df.iloc[0][c] for c in waste_cats]
        })
        if not comp_data.empty and comp_data["Value"].sum() > 0:
            render_donut(comp_data, "Value", "Category", f"Waste Breakdown ({latest})")

# --- H&S SUMMARY TABLE ---
if show_hs and not hs_df.empty:
    st.subheader("🦺 Health & Safety KPI Summary")
    hs_kpis_display = ["Fatalities", "Lost Time Injury", "First Aid Accident", 
                       "Near miss", "UA/UC Obsevations - Total number", 
                       "% of UA/UC Closure", "Safety observation worker involvement % [%]"]
    
    table_rows = []
    for kpi in hs_kpis_display:
        current = get_kpi_value(hs_df, kpi)
        target = get_kpi_value(hs_df, kpi)  # Adjust based on actual target column location
        lower = any(x in kpi.lower() for x in ["fatality", "injury", "accident", "near miss"])
        ach, _, status = calculate_status(current, target, lower)
        table_rows.append({"KPI": kpi[:40], "Actual": current, "Target": target, 
                          "Achievement %": ach, "Status": status})
    
    summary_df = pd.DataFrame(table_rows)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

# FOOTER
st.markdown("---")
st.caption(f"Last Refresh: {last_updated} | Source: GitHub | Built with Streamlit & Plotly")
