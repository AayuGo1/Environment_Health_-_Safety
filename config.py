# config.py
import streamlit as st

# Enterprise Color Palette (Dark Navy Theme)
COLORS = {
    "bg_primary": "#0B132B",       # Dark Navy Background
    "bg_secondary": "#1C2541",     # Slightly lighter navy for cards
    "bg_card": "#FFFFFF",          # White cards
    "text_primary": "#FFFFFF",     # White text on dark bg
    "text_secondary": "#A0AEC0",   # Grey text
    "text_dark": "#1A202C",        # Dark text on white cards
    "accent_green": "#38A169",     # Success / Target Met
    "accent_orange": "#DD6B20",    # Warning
    "accent_red": "#E53E3E",       # Danger / Missed Target
    "chart_blue": "#3182CE",       # Primary chart color
    "chart_teal": "#319795",       # Secondary chart color
}

# Layout Constants
PAGE_CONFIG = {
    "page_title": "EHS Dashboard | GNSC",
    "page_icon": "🛡️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# GitHub Configuration
GITHUB_REPO = "YOUR_USERNAME/YOUR_REPO_NAME"  # UPDATE THIS
GITHUB_BRANCH = "main"
EXCEL_FILENAME = "Monthly_KPI_Summary_Sheet_April_GNSC.xlsx"
RAW_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/"

def apply_custom_css():
    """Injects custom CSS for Glassmorphism and Enterprise feel."""
    st.markdown(f"""
        <style>
            /* Global Styles */
            .stApp {{ background-color: {COLORS['bg_primary']}; }}
            
            /* Card Styling */
            div[data-testid="stMetric"] {{
                background-color: {COLORS['bg_card']};
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border: 1px solid #E2E8F0;
            }}
            
            /* Metric Label & Value Colors */
            [data-testid="stMetricLabel"] > label {{ color: {COLORS['text_dark']} !important; font-weight: 600; }}
            [data-testid="stMetricValue"] {{ color: {COLORS['text_dark']} !important; font-size: 2rem !important; }}
            [data-testid="stMetricDelta"] {{ color: {COLORS['text_dark']} !important; }}
            
            /* Header Styling */
            .header-container {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 2rem;
                background-color: {COLORS['bg_secondary']};
                border-bottom: 1px solid #2D3748;
                margin-bottom: 2rem;
                border-radius: 0 0 16px 16px;
            }}
            .title {{ color: {COLORS['text_primary']}; font-size: 1.8rem; font-weight: 700; }}
            .subtitle {{ color: {COLORS['text_secondary']}; font-size: 0.9rem; }}
            
            /* Filter Panel */
            section[data-testid="stSidebar"] {{
                background-color: {COLORS['bg_secondary']};
                border-right: 1px solid #2D3748;
            }}
            .stSelectbox label, .stMultiSelect label {{ color: {COLORS['text_primary']} !important; }}
            
            /* Chart Containers */
            .chart-box {{
                background-color: {COLORS['bg_card']};
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
        </style>
    """, unsafe_allow_html=True)
