"""
Environment Performance Page Module
=====================================
Holistic environmental analytics covering production output,
water stewardship, waste management, and integrated sustainability
indicators with professional multi-panel visualization layout.
FIXED: Corrected data access pattern to use row_idx from kpi_metadata
instead of broken iloc[0] assumption. Matches Excel structure where
KPIs are ROWS and months are COLUMNS.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List

from config import THEME
from charts.line_chart import render_line_chart
from charts.donut import render_donut_chart
from analytics.calculations import compute_ytd_summary


def render_environment_page(parsed_data: Dict[str, Any]) -> None:
    """
    Renders the complete Environment Performance page.
    
    Args:
        parsed_data: Dictionary containing ParsedSheet objects.
    """
    env_sheet = parsed_data.get("Environment")
    if env_sheet is None:
        st.error(" Environment sheet required")
        return

    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h2 style="color: {THEME.TEXT_LIGHT}; font-size: 1.8rem;">🌿 Environmental Performance</h2>
            <p style="color: {THEME.TEXT_MUTED}; font-size: 0.95rem;">
                Production, water, and waste sustainability metrics
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Tabbed interface for domain separation
    tab_prod, tab_water, tab_waste = st.tabs(["Production", "Water Stewardship", "Waste Management"])

    with tab_prod:
        _render_production_section(env_sheet)
    
    with tab_water:
        _render_water_section(env_sheet)
    
    with tab_waste:
        _render_waste_section(env_sheet)


def _render_production_section(sheet: Any) -> None:
    """Renders production volume trend and intensity metrics."""
    vol_meta = _find_kpi_metadata(sheet, "Production Volume - Gross Weight")
    if not vol_meta:
        st.info("ℹ️ Production volume data not found")
        return
    
    row_idx = vol_meta["row_idx"]
    trend_df = _build_trend_df(sheet, [vol_meta["full_column"]], row_idx)
    
    fig = render_line_chart(
        df=trend_df, x_col="Month", y_cols=[vol_meta["full_column"]],
        title="Production Volume Trend", y_title="Metric Tonnes"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    ytd = compute_ytd_summary(
        df_wide=sheet.df_wide,
        row_idx=row_idx,
        ytd_column=sheet.ytd_column,
        month_columns=sheet.month_columns
    )
    st.metric("YTD Production Volume", f"{ytd:,.0f} MT" if ytd else "N/A")


def _render_water_section(sheet: Any) -> None:
    """Renders water withdrawal, recycling, and intensity metrics."""
    withdrawal_meta = _find_kpi_metadata(sheet, "Total water withdrawal  [m³/Gross Weight")
    recycle_pct_meta = _find_kpi_metadata(sheet, "% water re-used / recycled")
    
    cols_layout = st.columns(2)
    
    with cols_layout[0]:
        if withdrawal_meta:
            row_idx = withdrawal_meta["row_idx"]
            trend_df = _build_trend_df(sheet, [withdrawal_meta["full_column"]], row_idx)
            
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[withdrawal_meta["full_column"]],
                title="Water Intensity Trend", y_title="m³/MT",
                show_target=True, target_value=withdrawal_meta.get("target"),
                kpi_metadata={withdrawal_meta["full_column"]: withdrawal_meta}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with cols_layout[1]:
        if recycle_pct_meta:
            row_idx = recycle_pct_meta["row_idx"]
            trend_df = _build_trend_df(sheet, [recycle_pct_meta["full_column"]], row_idx)
            
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[recycle_pct_meta["full_column"]],
                title="Water Recycling Rate", y_title="%"
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_waste_section(sheet: Any) -> None:
    """Renders waste generation trends and composition breakdown."""
    waste_intensity_meta = _find_kpi_metadata(sheet, "Total waste per t(Metrics)")
    
    cols_layout = st.columns([2, 1])
    
    with cols_layout[0]:
        if waste_intensity_meta:
            row_idx = waste_intensity_meta["row_idx"]
            trend_df = _build_trend_df(sheet, [waste_intensity_meta["full_column"]], row_idx)
            
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[waste_intensity_meta["full_column"]],
                title="Waste Intensity Trend", y_title="kg/MT",
                kpi_metadata={waste_intensity_meta["full_column"]: waste_intensity_meta}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with cols_layout[1]:
        # Waste composition donut - find all waste category KPIs
        waste_cat_keywords = ["recycled", "landfill", "incineration", "composting", "reused"]
        waste_cats: List[Dict[str, Any]] = []
        
        for kpi_name, meta in sheet.kpi_metadata.items():
            if any(kw in kpi_name.lower() for kw in waste_cat_keywords):
                row_idx = meta.get("row_idx")
                if row_idx is None:
                    continue
                    
                ytd = compute_ytd_summary(
                    df_wide=sheet.df_wide,
                    row_idx=row_idx,
                    ytd_column=sheet.ytd_column,
                    month_columns=sheet.month_columns
                )
                
                if ytd and ytd > 0:
                    waste_cats.append({
                        "Category": kpi_name[:35],
                        "YTD kg": round(ytd, 1),
                        "row_idx": row_idx
                    })
        
        if waste_cats:
            comp_df = pd.DataFrame(waste_cats)
            fig = render_donut_chart(
                df=comp_df, values_col="YTD kg", names_col="Category",
                title="Waste Composition (YTD)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ No waste composition data available")


def _find_kpi_metadata(sheet: Any, partial_name: str) -> Optional[Dict]:
    """Finds KPI metadata by partial name match."""
    if not hasattr(sheet, 'kpi_metadata'):
        return None
        
    for kpi_name, meta in sheet.kpi_metadata.items():
        if partial_name.lower() in kpi_name.lower():
            return meta
    return None


def _build_trend_df(sheet: Any, columns: List[str], row_idx: int) -> pd.DataFrame:
    """
    Creates long-format trend dataframe for a SPECIFIC KPI row.
    FIXED: Uses row_idx instead of iloc[0] to get correct KPI data.
    
    Args:
        sheet: ParsedSheet object with df_wide and month_columns.
        columns: List of column names to extract (should be single KPI column).
        row_idx: Integer index of the KPI row in df_wide.
        
    Returns:
        DataFrame with 'Month' column and KPI value columns.
    """
    rows = []
    for mc in sheet.month_columns:
        row = {"Month": mc}
        for col in columns:
            if col in sheet.df_wide.columns:
                try:
                    val = sheet.df_wide.loc[sheet.df_wide.index[row_idx], mc]
                    # Handle percentage strings
                    if isinstance(val, str) and '%' in val:
                        val = float(val.replace('%', ''))
                    row[col] = float(val)
                except (ValueError, TypeError, KeyError, IndexError):
                    row[col] = None
        rows.append(row)
    return pd.DataFrame(rows)
