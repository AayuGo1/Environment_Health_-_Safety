"""
Executive Summary Page Module
===============================
Top-level dashboard view displaying aggregated KPI performance,
overall achievement status, and cross-domain trend indicators.
Serves as the primary landing page for senior management review.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from config import THEME
from components.cards import render_kpi_card
from analytics.calculations import calculate_achievement, extract_sparkline_data, compute_ytd_summary


def render_executive_summary(parsed_data: Dict[str, Any]) -> None:
    """
    Renders the complete Executive Summary page.
    
    Args:
        parsed_data: Dictionary containing ParsedSheet objects keyed by category.
                     Expected keys: 'Environment', 'Health & Safety'.
    """
    st.markdown(f"""
        <div style="
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, {THEME.BG_SECONDARY} 0%, {THEME.BG_TERTIARY} 100%);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        ">
            <h2 style="color: {THEME.TEXT_LIGHT}; margin: 0; font-size: 1.8rem;">
                📊 Executive Summary
            </h2>
            <p style="color: {THEME.TEXT_MUTED}; margin: 0.5rem 0 0 0; font-size: 0.95rem;">
                Consolidated EHS performance overview across all operational domains
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Extract key KPIs dynamically from parsed data
    env_sheet = parsed_data.get("Environment")
    hs_sheet = parsed_data.get("Health & Safety")
    
    if env_sheet is None:
        st.warning("⚠️ Environment sheet not found in workbook")
        return

    # Define priority KPIs for executive view (discovered dynamically)
    priority_kpis = _identify_priority_kpis(env_sheet, hs_sheet)
    
    # Render KPI cards in responsive grid
    cols = st.columns(min(len(priority_kpis), 4))
    for idx, kpi_info in enumerate(priority_kpis):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            _render_executive_kpi_card(kpi_info, env_sheet, hs_sheet)

    # Overall Performance Status Section
    st.divider()
    _render_overall_status_section(parsed_data)


def _identify_priority_kpis(env_sheet, hs_sheet) -> list:
    """Identifies top-priority KPIs for executive display based on metadata."""
    priority = []
    
    # From Environment sheet - select one representative per subcategory
    env_meta = env_sheet.kpi_metadata
    seen_categories = set()
    
    for kpi_name, meta in env_meta.items():
        cat = meta.get("category", "")
        if cat not in seen_categories and meta.get("target") is not None:
            priority.append({
                "name": kpi_name,
                "metadata": meta,
                "source": "environment",
                "sheet": env_sheet,
            })
            seen_categories.add(cat)
            
        if len(priority) >= 4:
            break
    
    # Add critical H&S KPIs if available
    if hs_sheet:
        hs_meta = hs_sheet.kpi_metadata
        for kpi_name, meta in hs_meta.items():
            if any(kw in kpi_name.lower() for kw in ["fatality", "injury", "closure"]):
                if meta.get("target") is not None and len(priority) < 6:
                    priority.append({
                        "name": kpi_name,
                        "metadata": meta,
                        "source": "health_safety",
                        "sheet": hs_sheet,
                    })
    
    return priority[:6]  # Max 6 executive KPIs


def _render_executive_kpi_card(kpi_info: dict, env_sheet, hs_sheet) -> None:
    """Renders a single executive KPI card with full metrics."""
    name = kpi_info["name"]
    meta = kpi_info["metadata"]
    sheet = kpi_info["sheet"]
    
    # Get current value (first row = latest month)
    col = meta["full_column"]
    try:
        current_val = float(sheet.df_wide.iloc[0][col])
    except (ValueError, TypeError, IndexError):
        current_val = None
    
    # Calculate achievement
    target = meta.get("target")
    lower_better = meta.get("lower_is_better", False)
    achievement, variance, status = calculate_achievement(current_val, target, lower_better)
    
    # Extract sparkline data
    sparkline = extract_sparkline_data(
        sheet.df_wide, col, sheet.month_columns
    )
    
    # Compute YTD
    ytd = compute_ytd_summary(sheet.df_wide, col, sheet.ytd_column)
    
    # Get unit from metadata
    unit = meta.get("unit", "")
    
    render_kpi_card(
        title=name,
        value=current_val,
        unit=unit,
        target=target,
        achievement=achievement,
        status=status,
        sparkline_data=sparkline,
        ytd_value=ytd,
    )


def _render_overall_status_section(parsed_data: Dict[str, Any]) -> None:
    """Renders aggregate performance status across all domains."""
    total_kpis = 0
    on_track = 0
    off_track = 0
    
    for category, sheet in parsed_data.items():
        for kpi_name, meta in sheet.kpi_metadata.items():
            if meta.get("target") is None:
                continue
                
            col = meta["full_column"]
            try:
                val = float(sheet.df_wide.iloc[0][col])
            except (ValueError, TypeError):
                continue
            
            _, _, status = calculate_achievement(
                val, meta["target"], meta.get("lower_is_better", False)
            )
            total_kpis += 1
            if "On Track" in status:
                on_track += 1
            else:
                off_track += 1
    
    if total_kpis == 0:
        st.info("ℹ️ No KPIs with targets found for status calculation")
        return
    
    pct_on_track = round((on_track / total_kpis) * 100, 1)
    
    st.markdown(f"""
        <div style="
            display: flex; justify-content: space-around; align-items: center;
            padding: 2rem;
            background: {THEME.CARD_BG};
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-top: 1rem;
        ">
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 700; color: {THEME.CHART_PRIMARY};">
                    {total_kpis}
                </div>
                <div style="color: {THEME.TEXT_DARK}; font-weight: 600;">Total KPIs</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 700; color: {THEME.STATUS_ON_TRACK};">
                    {on_track}
                </div>
                <div style="color: {THEME.TEXT_DARK}; font-weight: 600;">On Track</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 700; color: {THEME.STATUS_OFF_TRACK};">
                    {off_track}
                </div>
                <div style="color: {THEME.TEXT_DARK}; font-weight: 600;">Off Track</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 700; color: {THEME.CHART_ACCENT_1};">
                    {pct_on_track}%
                </div>
                <div style="color: {THEME.TEXT_DARK}; font-weight: 600;">Achievement Rate</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
