"""
Energy Performance Page Module
================================
Comprehensive energy analytics view featuring intensity trends,
consumption source breakdowns, renewable energy contribution,
and efficiency target tracking with professional Plotly charts.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from config import THEME
from charts.line_chart import render_line_chart
from charts.donut import render_donut_chart
from analytics.calculations import extract_sparkline_data, compute_ytd_summary


def render_energy_page(parsed_data: Dict[str, Any]) -> None:
    """
    Renders the complete Energy Performance page.
    
    Args:
        parsed_data: Dictionary containing ParsedSheet objects.
    """
    env_sheet = parsed_data.get("Environment")
    if env_sheet is None:
        st.error(" Environment sheet required for Energy page")
        return

    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h2 style="color: {THEME.TEXT_LIGHT}; font-size: 1.8rem;"> Energy Performance</h2>
            <p style="color: {THEME.TEXT_MUTED}; font-size: 0.95rem;">
                Consumption analysis, intensity trends, and efficiency metrics
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- Energy Intensity Trend ---
    st.subheader("Energy Intensity Trend")
    intensity_col = _find_kpi_column(env_sheet, "Total energy consumption [kWh/Gross Weight")
    if intensity_col:
        trend_df = _build_trend_dataframe(env_sheet, [intensity_col])
        meta = env_sheet.kpi_metadata.get(
            next(k for k, v in env_sheet.kpi_metadata.items() if v["full_column"] == intensity_col), {}
        )
        fig = render_line_chart(
            df=trend_df,
            x_col="Month",
            y_cols=[intensity_col],
            title="Energy Intensity (kWh/MT)",
            y_title="kWh per Metric Tonne",
            show_target=True,
            target_value=meta.get("target"),
            kpi_metadata={intensity_col: meta},
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Consumption Source Breakdown ---
    st.subheader("Energy Consumption by Source (YTD)")
    source_cols = [
        c for c in env_sheet.df_wide.columns 
        if ("electricity" in c.lower() or "diesel" in c.lower() or 
            "png" in c.lower() or "lpg" in c.lower())
        and "consumption" not in c.lower()
    ]
    
    if source_cols:
        ytd_values = []
        labels = []
        for col in source_cols:
            kpi_name = next(
                (k for k, v in env_sheet.kpi_metadata.items() if v["full_column"] == col),
                col.split("|")[-1].strip()
            )
            ytd = compute_ytd_summary(env_sheet.df_wide, col, env_sheet.ytd_column)
            if ytd and ytd > 0:
                ytd_values.append(ytd)
                labels.append(kpi_name[:30])
        
        if ytd_values:
            donut_df = pd.DataFrame({"Source": labels, "YTD Consumption": ytd_values})
            fig = render_donut_chart(
                df=donut_df,
                values_col="YTD Consumption",
                names_col="Source",
                title="Energy Mix Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Renewable Energy Contribution ---
    st.subheader("Renewable Energy Contribution")
    renewable_cols = [
        c for c in env_sheet.df_wide.columns
        if "renewable" in c.lower() and ("generated" in c.lower() or "ppa" in c.lower() or "certificate" in c.lower())
    ]
    
    total_renewable_ytd = sum(
        compute_ytd_summary(env_sheet.df_wide, c, env_sheet.ytd_column) or 0
        for c in renewable_cols
    )
    
    total_energy_col = _find_kpi_column(env_sheet, "Total energy consumption [kWh]")
    total_energy_ytd = compute_ytd_summary(env_sheet.df_wide, total_energy_col, env_sheet.ytd_column) if total_energy_col else None
    
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


def _find_kpi_column(sheet, partial_name: str) -> str | None:
    """Finds column matching partial KPI name."""
    for kpi_name, meta in sheet.kpi_metadata.items():
        if partial_name.lower() in kpi_name.lower():
            return meta["full_column"]
    return None


def _build_trend_dataframe(sheet, columns: list) -> pd.DataFrame:
    """Builds long-format dataframe for trend charting."""
    rows = []
    for mc in sheet.month_columns:
        row = {"Month": mc}
        for col in columns:
            if col in sheet.df_wide.columns:
                row[col] = sheet.df_wide.iloc[0][col]
        rows.append(row)
    return pd.DataFrame(rows)
