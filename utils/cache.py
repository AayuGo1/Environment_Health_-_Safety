"""
Streamlit-native caching wrapper for GitHub data persistence.
Uses st.session_state for cross-rerun persistence and 
st.cache_data for function-level memoization.
Ensures fresh data loads when 'Refresh' is clicked while
preventing redundant API calls during normal interaction.
"""

import streamlit as st
from typing import Optional, Tuple
import pandas as pd


def get_cached_data(force_stale: bool = False) -> Optional[Tuple[pd.ExcelFile, str]]:
    """
    Retrieves cached Excel data if available and not forced stale.
    
    Args:
        force_stale: If True, ignores cache and forces fresh load.
        
    Returns:
        Tuple of (ExcelFile object, timestamp string) or None.
    """
    if force_stale:
        return None
    
    cached = st.session_state.get("_cached_excel_data", None)
    if cached is None:
        return None
        
    # Validate cache integrity
    try:
        xls, ts = cached
        if isinstance(xls, pd.ExcelFile):
            return cached
    except (ValueError, TypeError, AttributeError):
        pass
        
    return None


def set_cached_data(xls: pd.ExcelFile, timestamp: str) -> None:
    """
    Stores Excel data in session state for cross-rerun persistence.
    
    Args:
        xls: Parsed ExcelFile object from pandas.
        timestamp: Human-readable timestamp of data freshness.
    """
    st.session_state["_cached_excel_data"] = (xls, timestamp)


def clear_dashboard_cache() -> None:
    """
    Clears both Streamlit's function cache and session state cache.
    Must be called when user clicks 'Refresh Data' to ensure
    latest GitHub content is fetched.
    """
    st.cache_data.clear()
    if "_cached_excel_data" in st.session_state:
        del st.session_state["_cached_excel_data"]
