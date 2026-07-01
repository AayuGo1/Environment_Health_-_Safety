"""
Sidebar Filter Component Module
=================================
Professional left-side filter panel with dynamic content discovery,
persistent user selections via session state, and instant dashboard
refresh capabilities. Adapts automatically to new months/KPIs in Excel.
"""

import streamlit as st
from typing import List, Dict, Any

from config import THEME
from utils.cache import clear_dashboard_cache


def render_sidebar(month_columns: List[str]) -> Dict[str, Any]:
    """
    Renders the complete sidebar filter interface.
    
    Args:
        month_columns: Dynamically detected list of month column names
                       from the Excel workbook (e.g., ['Apr-25', 'May-25']).
                       
    Returns:
        Dictionary of active filter selections for downstream use.
    """
    # Initialize session state for filter persistence
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "financial_year": "2025-2026",
            "month": "All",
            "show_energy": True,
            "show_water": True,
            "show_waste": True,
            "show_hs": True,
            "show_environment": True,
        }

    with st.sidebar:
        # Branding & Refresh Section
        st.markdown(f"""
            <div style="
                padding: 1rem 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                margin-bottom: 1.5rem;
            ">
                <div style="
                    color: {THEME.TEXT_LIGHT};
                    font-size: 1.1rem;
                    font-weight: 700;
                    margin-bottom: 1rem;
                ">🔍 Dashboard Filters</div>
            </div>
        """, unsafe_allow_html=True)

        # Primary Action Button
        if st.button(
            " Refresh Data",
            use_container_width=True,
            type="primary",
            help="Clear cache and reload latest data from GitHub"
        ):
            clear_dashboard_cache()
            st.rerun()

        st.divider()

        # Time Period Filters
        st.markdown(f"""
            <div style="
                color: {THEME.TEXT_MUTED};
                font-size: 0.7rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 0.5rem;
            ">Time Period</div>
        """, unsafe_allow_html=True)

        fy_options = ["2025-2026"]  # Dynamic in future versions
        st.session_state.filters["financial_year"] = st.selectbox(
            "Financial Year",
            options=fy_options,
            index=fy_options.index(st.session_state.filters["financial_year"]),
            label_visibility="collapsed"
        )

        month_options = ["All"] + sorted(month_columns, key=lambda x: x.split("-")[::-1])
        st.session_state.filters["month"] = st.selectbox(
            "Month",
            options=month_options,
            index=month_options.index(st.session_state.filters["month"]) 
                  if st.session_state.filters["month"] in month_options else 0,
            label_visibility="collapsed"
        )

        st.divider()

        # Category Toggles
        st.markdown(f"""
            <div style="
                color: {THEME.TEXT_MUTED};
                font-size: 0.7rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 0.5rem;
            ">KPI Categories</div>
        """, unsafe_allow_html=True)

        categories = [
            ("⚡ Energy", "show_energy"),
            ("💧 Water", "show_water"),
            ("♻️ Waste", "show_waste"),
            ("🌿 Environment", "show_environment"),
            ("🦺 Health & Safety", "show_hs"),
        ]

        for label, key in categories:
            st.session_state.filters[key] = st.checkbox(
                label,
                value=st.session_state.filters[key],
                label_visibility="visible"
            )

        # Reset Option
        st.divider()
        if st.button("Reset All Filters", use_container_width=True):
            st.session_state.filters = {
                "financial_year": "2025-2026",
                "month": "All",
                "show_energy": True,
                "show_water": True,
                "show_waste": True,
                "show_hs": True,
                "show_environment": True,
            }
            st.rerun()

    return st.session_state.filters
