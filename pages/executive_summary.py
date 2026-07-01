"""
Executive Summary Page Module
===============================
Top-level dashboard view displaying aggregated KPI performance,
overall achievement status, and cross-domain trend indicators.
FIXED: Corrected data access pattern to use row_idx from kpi_metadata
instead of broken iloc[0] assumption. Matches Excel structure where
KPIs are ROWS and months are COLUMNS.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional

from config import THEME
from components.cards import render_kpi_card
from analytics.calculations import (
    calculate_achievement, 
    extract_sparkline_data, 
    compute_ytd_summary
)


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
    
    if env_sheet is None and hs_sheet is None:
        st.warning("️ No data sheets found in workbook")
        return

    # Define priority KPIs for executive view (discovered dynamically)
    priority_kpis = _identify_priority_kpis(env_sheet, hs_sheet)
    
    if not priority_kpis:
        st.info("ℹ️ No KPIs with valid data found for executive summary")
        return
    
    # Render KPI cards in responsive grid
    cols = st.columns(min(len(priority_kpis), 4))
    for idx, kpi_info in enumerate(priority_kpis):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            _render_executive_kpi_card(kpi_info)

    # Overall Performance Status Section
    st.divider()
    _render_overall_status_section(parsed_data)


def _identify_priority_kpis(env_sheet: Optional[Any], hs_sheet: Optional[Any]) -> List[Dict]:
    """Identifies top-priority KPIs for executive display based on metadata."""
    priority = []
    seen_categories = set()
    
    # Process Environment sheet first
    if env_sheet and hasattr(env_sheet, 'kpi_metadata'):
        for kpi_name, meta in env_sheet.kpi_metadata.items():
            cat = meta.get("category", "")
            row_idx = meta.get("row_idx")
            
            # Skip if no row index or already seen this category
            if row_idx is None or cat in seen_categories:
                continue
                
            # Validate that this KPI has actual numeric data
            try:
                test_val = float(env_sheet.df_wide.loc[env_sheet.df_wide.index[row_idx], env_sheet.month_columns[0]])
                if pd.isna(test_val):
                    continue
            except (ValueError, TypeError, KeyError, IndexError):
                continue
            
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
    if hs_sheet and hasattr(hs_sheet, 'kpi_metadata'):
        for kpi_name, meta in hs_sheet.kpi_metadata.items():
            if any(kw in kpi_name.lower() for kw in ["fatality", "injury", "closure"]):
                row_idx = meta.get("row_idx")
                if row_idx is None:
                    continue
                    
                # Validate data exists
                try:
                    test_val = float(hs_sheet.df_wide.loc[hs_sheet.df_wide.index[row_idx], hs_sheet.month_columns[0]])
                    if pd.isna(test_val):
                        continue
                except (ValueError, TypeError, KeyError, IndexError):
                    continue
                    
                if len(priority) < 6:
                    priority.append({
                        "name": kpi_name,
                        "metadata": meta,
                        "source": "health_safety",
                        "sheet": hs_sheet,
                    })
    
    return priority[:6]  # Max 6 executive KPIs


def _render_executive_kpi_card(kpi_info: Dict) -> None:
    """Renders a single executive KPI card with full metrics."""
    name = kpi_info["name"]
    meta = kpi_info["metadata"]
    sheet = kpi_info["sheet"]
    row_idx = meta.get("row_idx")
    
    if row_idx is None:
        st.metric(label=name, value="N/A", delta="Missing Row Index")
        return
    
    # Get current value (latest month column)
    latest_month = sheet.month_columns[-1] if sheet.month_columns else None
    current_val = None
    if latest_month and latest_month in sheet.df_wide.columns:
        try:
            raw_val = sheet.df_wide.loc[sheet.df_wide.index[row_idx], latest_month]
            if isinstance(raw_val, str) and '%' in raw_val:
                current_val = float(raw_val.replace('%', ''))
            else:
                current_val = float(raw_val)
        except (ValueError, TypeError, KeyError, IndexError):
            current_val = None
    
    # Calculate achievement
    target = meta.get("target")
    lower_better = meta.get("lower_is_better", False)
    achievement, variance, status = calculate_achievement(current_val, target, lower_better)
    
    # Extract sparkline data using correct row index
    sparkline = extract_sparkline_data(
        df_wide=sheet.df_wide,
        row_idx=row_idx,
        month_columns=sheet.month_columns
    )
    
    # Compute YTD using correct row index
    ytd = compute_ytd_summary(
        df_wide=sheet.df_wide,
        row_idx=row_idx,
        ytd_column=sheet.ytd_column,
        month_columns=sheet.month_columns
    )
    
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
        if not hasattr(sheet, 'kpi_metadata'):
            continue
            
        for kpi_name, meta in sheet.kpi_metadata.items():
            target = meta.get("target")
            if target is None:
                continue
                
            row_idx = meta.get("row_idx")
            if row_idx is None:
                continue
                
            # Get latest month value for this KPI
            latest_month = sheet.month_columns[-1] if sheet.month_columns else None
            if not latest_month or latest_month not in sheet.df_wide.columns:
                continue
                
            try:
                raw_val = sheet.df_wide.loc[sheet.df_wide.index[row_idx], latest_month]
                if isinstance(raw_val, str) and '%' in raw_val:
                    val = float(raw_val.replace('%', ''))
                else:
                    val = float(raw_val)
                    
                if pd.isna(val):
                    continue
                    
                _, _, status = calculate_achievement(
                    val, target, meta.get("lower_is_better", False)
                )
                total_kpis += 1
                if "On Track" in status:
                    on_track += 1
                else:
                    off_track += 1
            except (ValueError, TypeError, KeyError, IndexError):
                continue
    
    if total_kpis == 0:
        st.info("ℹ️ No KPIs with targets and valid data found for status calculation")
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
