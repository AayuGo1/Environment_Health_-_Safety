"""
Enterprise EHS Dashboard - Main Application Orchestrator
==========================================================
Central entry point that coordinates all components, pages, and services.
FIXED: Added robust error handling for page rendering and data validation.
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any

from config import THEME, GITHUB, PAGE
from utils.github_loader import GitHubDataLoader
from utils.excel_parser import ExcelParser
from utils.cache import get_cached_data, set_cached_data, clear_dashboard_cache
from components.header import render_header, update_timestamp_js
from components.sidebar import render_sidebar
from pages.executive_summary import render_executive_summary
from pages.environment import render_environment_page
from pages.energy import render_energy_page
from pages.health_safety import render_health_safety_page
from pages.analytics import render_analytics_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_session_state() -> None:
    """Initializes persistent session state variables."""
    defaults = {
        "parsed_data": None,
        "last_updated": None,
        "load_error": None,
        "active_page": "Executive Summary",
        "search_query": "",
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def load_and_parse_data() -> bool:
    """Loads Excel from GitHub and parses into normalized structures."""
    loader = GitHubDataLoader()
    result = loader.load_workbook()
    
    if result is None:
        st.session_state.load_error = "Failed to load data from GitHub"
        st.session_state.parsed_data = None
        return False
    
    xls, timestamp = result
    parser = ExcelParser(xls)
    parsed = parser.parse_all()
    
    if not parsed:
        st.session_state.load_error = "No recognizable sheets found in workbook"
        st.session_state.parsed_data = None
        return False
    
    st.session_state.parsed_data = parsed
    st.session_state.last_updated = timestamp
    st.session_state.load_error = None
    logger.info(f"Data loaded successfully. Timestamp: {timestamp}")
    return True


def render_global_search() -> None:
    """Renders global search bar."""
    query = st.text_input(
        "🔍 Search KPIs...",
        value=st.session_state.search_query,
        placeholder="e.g., Energy, Water, Fatality...",
        label_visibility="collapsed",
    )
    st.session_state.search_query = query


def render_page_content(page_name: str, parsed_data: Dict[str, Any]) -> None:
    """Routes to appropriate page renderer with error handling."""
    page_map = {
        "Executive Summary": render_executive_summary,
        "Environment": render_environment_page,
        "Energy": render_energy_page,
        "Health & Safety": render_health_safety_page,
        "Analytics": render_analytics_page,
    }
    
    renderer = page_map.get(page_name)
    if renderer:
        try:
            if parsed_data:
                renderer(parsed_data)
            else:
                st.warning("⚠️ No data available. Please refresh.")
        except Exception as e:
            st.error(f"❌ Error loading '{page_name}': {str(e)}")
            logger.exception(f"Page render error: {page_name}")
            st.code(str(e), language="python")
    else:
        st.warning(f"⚠️ Page '{page_name}' is under development")


def render_error_state() -> None:
    """Renders professional error page when data loading fails."""
    st.markdown(f"""
        <div style="
            text-align: center; padding: 4rem 2rem;
            background: {THEME.BG_SECONDARY}; border-radius: 16px;
            margin-top: 4rem;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
            <h2 style="color: {THEME.TEXT_LIGHT};">Dashboard Unavailable</h2>
            <p style="color: {THEME.TEXT_MUTED}; max-width: 600px; margin: 1rem auto;">
                {st.session_state.load_error}<br/><br/>
                Please verify your GitHub repository is accessible.
            </p>
        </div>
    """, unsafe_allow_html=True)


def main() -> None:
    """Primary application execution flow."""
    st.set_page_config(
        page_title=PAGE.TITLE,
        page_icon=PAGE.ICON,
        layout=PAGE.LAYOUT,
        initial_sidebar_state=PAGE.SIDEBAR_STATE,
    )
    
    initialize_session_state()
    
    # Render Header
    render_header(st.session_state.last_updated or "Loading...")
    
    # Global Search Bar
    render_global_search()
    
    # Load Data
    if st.session_state.parsed_data is None:
        with st.spinner("Loading EHS data from GitHub..."):
            success = load_and_parse_data()
            if success:
                update_timestamp_js(st.session_state.last_updated)
    
    # Error State
    if st.session_state.load_error:
        render_error_state()
        return
    
    # Sidebar Navigation & Filters
    parsed_data = st.session_state.parsed_data
    month_cols = []
    if parsed_data and "Environment" in parsed_data:
        month_cols = parsed_data["Environment"].month_columns
    
    filters = render_sidebar(month_cols)
    
    # Page Navigation Tabs
    page_names = ["Executive Summary", "Environment", "Energy", "Health & Safety", "Analytics"]
    st.session_state.active_page = st.segmented_control(
        "Dashboard Section",
        options=page_names,
        default=st.session_state.active_page,
        label_visibility="collapsed",
    )
    
    # Render Selected Page
    render_page_content(st.session_state.active_page, parsed_data)
    
    # Footer / Debug
    st.divider()
    st.caption(f"Last Refresh: {st.session_state.last_updated or 'N/A'} | v1.0")


if __name__ == "__main__":
    main()
