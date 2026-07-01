# utils/cache.py
"""
Streamlit-native caching wrapper for GitHub data persistence.
Uses st.cache_data with TTL to prevent redundant API calls while
ensuring fresh data loads when 'Refresh' is clicked.
"""

import streamlit as st
from typing import Optional, Tuple
import pandas as pd


def get_cached_data(force_stale: bool = False) -> Optional[Tuple[pd.ExcelFile, str]]:
    """Retrieves cached Excel data if available and not forced stale."""
    if force_stale:
        return None
    return st.session_state.get("_cached_excel_data", None)


def set_cached_data(xls: pd.ExcelFile, timestamp: str) -> None:
    """Stores Excel data in session state for cross-rerun persistence."""
    st.session_state["_cached_excel_data"] = (xls, timestamp)


def clear_dashboard_cache() -> None:
    """Clears both Streamlit's function cache and session state cache."""
    st.cache_data.clear()
    if "_cached_excel_data" in st.session_state:
        del st.session_state["_cached_excel_data"]
