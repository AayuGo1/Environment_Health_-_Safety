"""
Environment Performance Page Module
=====================================
Holistic environmental analytics covering production output,
water stewardship, waste management, and integrated sustainability
indicators with professional multi-panel visualization layout.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

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
        st.error("❌ Environment sheet required")
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


def _render_production_section(sheet) -> None:
    """Renders production volume trend and intensity metrics."""
    vol_col = _find_col(sheet, "Production Volume - Gross Weight")
    if vol_col:
        trend_df = _build_trend_df(sheet, [vol_col])
        fig = render_line_chart(
            df=trend_df, x_col="Month", y_cols=[vol_col],
            title="Production Volume Trend", y_title="Metric Tonnes"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        ytd = compute_ytd_summary(sheet.df_wide, vol_col, sheet.ytd_column)
        st.metric("YTD Production Volume", f"{ytd:,.0f} MT" if ytd else "N/A")


def _render_water_section(sheet) -> None:
    """Renders water withdrawal, recycling, and intensity metrics."""
    withdrawal_col = _find_col(sheet, "Total water withdrawal  [m³/Gross Weight")
    recycle_pct_col = _find_col(sheet, "% water re-used / recycled")
    
    cols_layout = st.columns(2)
    
    with cols_layout[0]:
        if withdrawal_col:
            trend_df = _build_trend_df(sheet, [withdrawal_col])
            meta = sheet.kpi_metadata.get(
                next(k for k, v in sheet.kpi_metadata.items() if v["full_column"] == withdrawal_col), {}
            )
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[withdrawal_col],
                title="Water Intensity Trend", y_title="m³/MT",
                show_target=True, target_value=meta.get("target"),
                kpi_metadata={withdrawal_col: meta}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with cols_layout[1]:
        if recycle_pct_col:
            trend_df = _build_trend_df(sheet, [recycle_pct_col])
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[recycle_pct_col],
                title="Water Recycling Rate", y_title="%"
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_waste_section(sheet) -> None:
    """Renders waste generation trends and composition breakdown."""
    waste_intensity_col = _find_col(sheet, "Total waste per t(Metrics)")
    total_waste_col = _find_col(sheet, "Total waste [kg]")
    
    cols_layout = st.columns([2, 1])
    
    with cols_layout[0]:
        if waste_intensity_col:
            trend_df = _build_trend_df(sheet, [waste_intensity_col])
            meta = sheet.kpi_metadata.get(
                next(k for k, v in sheet.kpi_metadata.items() if v["full_column"] == waste_intensity_col), {}
            )
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[waste_intensity_col],
                title="Waste Intensity Trend", y_title="kg/MT",
                kpi_metadata={waste_intensity_col: meta}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with cols_layout[1]:
        # Waste composition donut
        waste_cat_cols = [
            c for c in sheet.df_wide.columns
            if ("recycled" in c.lower() or "landfill" in c.lower() or "incineration" in c.lower())
            and "waste" in c.lower()
        ]
        
        if waste_cat_cols:
            comp_data = []
            for col in waste_cat_cols:
                kpi_name = next(
                    (k for k, v in sheet.kpi_metadata.items() if v["full_column"] == col),
                    col.split("|")[-1].strip()[:30]
                )
                ytd = compute_ytd_summary(sheet.df_wide, col, sheet.ytd_column)
                if ytd and ytd > 0:
                    comp_data.append({"Category": kpi_name, "YTD kg": ytd})
            
            if comp_data:
                donut_df = pd.DataFrame(comp_data)
                fig = render_donut_chart(
                    df=donut_df, values_col="YTD kg", names_col="Category",
                    title="Waste Composition (YTD)"
                )
                st.plotly_chart(fig, use_container_width=True)


def _find_col(sheet, partial: str) -> str | None:
    """Finds column by partial name match."""
    for kpi_name, meta in sheet.kpi_metadata.items():
        if partial.lower() in kpi_name.lower():
            return meta["full_column"]
    return None


def _build_trend_df(sheet, columns: list) -> pd.DataFrame:
    """Creates long-format trend dataframe."""
    rows = []
    for mc in sheet.month_columns:
        row = {"Month": mc}
        for col in columns:
            if col in sheet.df_wide.columns:
                row[col] = sheet.df_wide.iloc[0][col]
        rows.append(row)
    return pd.DataFrame(rows)
