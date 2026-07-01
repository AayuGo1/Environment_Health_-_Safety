"""
Energy Performance Page Module
================================
Comprehensive energy analytics view featuring intensity trends,
consumption source breakdowns, renewable energy contribution,
and efficiency target tracking with professional Plotly charts.
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


def render_energy_page(parsed_data: Dict[str, Any]) -> None:
    """
    Renders the complete Energy Performance page.
    
    Args:
        parsed_data: Dictionary containing ParsedSheet objects.
    """
    env_sheet = parsed_data.get("Environment")
    if env_sheet is None:
        st.error("❌ Environment sheet required for Energy page")
        return

    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h2 style="color: {THEME.TEXT_LIGHT}; font-size: 1.8rem;">⚡ Energy Performance</h2>
            <p style="color: {THEME.TEXT_MUTED}; font-size: 0.95rem;">
                Consumption analysis, intensity trends, and efficiency metrics
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- Energy Intensity Trend ---
    st.subheader("Energy Intensity Trend")
    intensity_meta = _find_kpi_metadata(env_sheet, "Total energy consumption [kWh/Gross Weight")
    if intensity_meta:
        row_idx = intensity_meta["row_idx"]
        trend_df = _build_trend_df(env_sheet, [intensity_meta["full_column"]], row_idx)
        
        fig = render_line_chart(
            df=trend_df,
            x_col="Month",
            y_cols=[intensity_meta["full_column"]],
            title="Energy Intensity (kWh/MT)",
            y_title="kWh per Metric Tonne",
            show_target=True,
            target_value=intensity_meta.get("target"),
            kpi_metadata={intensity_meta["full_column"]: intensity_meta},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Energy intensity data not found")

    # --- Consumption Source Breakdown ---
    st.subheader("Energy Consumption by Source (YTD)")
    source_keywords = ["diesel", "lpg", "png", "grid electricity", "renewable"]
    source_data: List[Dict[str, Any]] = []
    
    for kpi_name, meta in env_sheet.kpi_metadata.items():
        if any(kw in kpi_name.lower() for kw in source_keywords):
            row_idx = meta.get("row_idx")
            if row_idx is None:
                continue
                
            ytd = compute_ytd_summary(
                df_wide=env_sheet.df_wide,
                row_idx=row_idx,
                ytd_column=env_sheet.ytd_column,
                month_columns=env_sheet.month_columns
            )
            
            if ytd and ytd > 0:
                source_data.append({
                    "Source": kpi_name[:35],
                    "YTD Consumption": round(ytd, 1),
                })
    
    if source_data:
        donut_df = pd.DataFrame(source_data)
        fig = render_donut_chart(
            df=donut_df,
            values_col="YTD Consumption",
            names_col="Source",
            title="Energy Mix Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No energy source breakdown data available")

    # --- Renewable Energy Contribution ---
    st.subheader("Renewable Energy Contribution")
    renewable_keywords = ["renewable", "ppa", "on-site", "certificate"]
    total_renewable_ytd = 0.0
    
    for kpi_name, meta in env_sheet.kpi_metadata.items():
        if any(kw in kpi_name.lower() for kw in renewable_keywords):
            row_idx = meta.get("row_idx")
            if row_idx is None:
                continue
                
            ytd = compute_ytd_summary(
                df_wide=env_sheet.df_wide,
                row_idx=row_idx,
                ytd_column=env_sheet.ytd_column,
                month_columns=env_sheet.month_columns
            )
            if ytd:
                total_renewable_ytd += ytd
    
    total_energy_meta = _find_kpi_metadata(env_sheet, "Total energy consumption [kWh]")
    total_energy_ytd = None
    if total_energy_meta:
        row_idx = total_energy_meta["row_idx"]
        total_energy_ytd = compute_ytd_summary(
            df_wide=env_sheet.df_wide,
            row_idx=row_idx,
            ytd_column=env_sheet.ytd_column,
            month_columns=env_sheet.month_columns
        )
    
    if total_energy_ytd and total_energy_ytd > 0:
        renewable_pct = round((total_renewable_ytd / total_energy_ytd) * 100, 1)
        st.metric(
            label="Renewable Energy Share (YTD)",
            value=f"{renewable_pct}%",
            delta=f"{total_renewable_ytd:,.0f} kWh renewable out of {total_energy_ytd:,.0f} kWh total",
            delta_color="inverse" if renewable_pct > 10 else "normal",
        )
    else:
        st.info("ℹ️ Insufficient data to calculate renewable contribution")


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
                    row[col] = float(val)
                except (ValueError, TypeError, KeyError, IndexError):
                    row[col] = None
        rows.append(row)
    return pd.DataFrame(rows)
