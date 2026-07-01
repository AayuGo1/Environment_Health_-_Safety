"""
Health & Safety Performance Page Module
=========================================
Dedicated H&S analytics view featuring lagging vs leading indicator
separation, TRIR/LTIFR frequency rate trends, UA/UC observation
closure tracking, and safety training effectiveness analysis.
Uses specialized chart types appropriate for safety data visualization.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from config import THEME
from charts.line_chart import render_line_chart
from analytics.calculations import calculate_achievement, compute_ytd_summary


def render_health_safety_page(parsed_data: Dict[str, Any]) -> None:
    """
    Renders the complete Health & Safety Performance page.
    
    Args:
        parsed_data: Dictionary containing ParsedSheet objects keyed by category.
    """
    hs_sheet = parsed_data.get("Health & Safety")
    if hs_sheet is None:
        st.error(" Health & Safety sheet not found in workbook")
        return

    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h2 style="color: {THEME.TEXT_LIGHT}; font-size: 1.8rem;">🦺 Health & Safety Performance</h2>
            <p style="color: {THEME.TEXT_MUTED}; font-size: 0.95rem;">
                Lagging indicators, leading observations, and safety culture metrics
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Tabbed interface separating indicator types
    tab_lagging, tab_leading, tab_rates, tab_training = st.tabs([
        "Lagging Indicators", "Leading Indicators", "Frequency Rates", "Safety Training"
    ])

    with tab_lagging:
        _render_lagging_indicators(hs_sheet)
    
    with tab_leading:
        _render_leading_indicators(hs_sheet)
    
    with tab_rates:
        _render_frequency_rates(hs_sheet)
    
    with tab_training:
        _render_safety_training(hs_sheet)


def _render_lagging_indicators(sheet) -> None:
    """Renders fatality, LTI, RWC, and first aid incident trends."""
    lagging_kpis = [
        "Fatalities",
        "Lost Time Injury",
        "Restricted work case (RWC)",
        "First Aid Accident",
        "Significant Near Miss",
    ]
    
    cols_to_plot = []
    for kpi_name in lagging_kpis:
        col = _find_hs_column(sheet, kpi_name)
        if col:
            cols_to_plot.append(col)
    
    if cols_to_plot:
        trend_df = _build_hs_trend_df(sheet, cols_to_plot)
        fig = render_line_chart(
            df=trend_df, x_col="Month", y_cols=cols_to_plot,
            title="Lagging Indicator Trends", y_title="Count",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # YTD Summary Cards
    summary_cols = st.columns(min(len(lagging_kpis), 4))
    for idx, kpi_name in enumerate(lagging_kpis):
        col = _find_hs_column(sheet, kpi_name)
        if col and idx < len(summary_cols):
            ytd = compute_ytd_summary(sheet.df_wide, col, sheet.ytd_column)
            with summary_cols[idx]:
                st.metric(
                    label=kpi_name,
                    value=f"{int(ytd)}" if ytd else "0",
                    delta="YTD Total",
                    delta_color="normal"
                )


def _render_leading_indicators(sheet) -> None:
    """Renders UA/UC observations, unsafe acts/conditions, and near miss trends."""
    leading_kpis = [
        "Near miss",
        "UA/UC Obsevations - Total number",
        "Unsafe Conditions - Total number",
        "Unsafe Act - Total Number",
    ]
    
    cols_to_plot = []
    for kpi_name in leading_kpis:
        col = _find_hs_column(sheet, kpi_name)
        if col:
            cols_to_plot.append(col)
    
    if cols_to_plot:
        trend_df = _build_hs_trend_df(sheet, cols_to_plot)
        fig = render_line_chart(
            df=trend_df, x_col="Month", y_cols=cols_to_plot,
            title="Leading Indicator Trends", y_title="Count",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # UA/UC Closure Rate Gauge
    closure_col = _find_hs_column(sheet, "% of UA/UC Closure")
    if closure_col:
        latest_val = sheet.df_wide.iloc[0][closure_col]
        try:
            closure_pct = float(str(latest_val).replace("%", ""))
            target_pct = 95.0  # Standard H&S target
            
            st.markdown(f"""
                <div style="
                    padding: 1.5rem; background: {THEME.CARD_BG};
                    border-radius: 12px; margin-top: 1rem;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                ">
                    <div style="color: {THEME.TEXT_DARK}; font-weight: 600; margin-bottom: 0.5rem;">
                        UA/UC Closure Rate (Latest Month)
                    </div>
                    <div style="font-size: 2.5rem; font-weight: 700; color: {
                        THEME.STATUS_ON_TRACK if closure_pct >= target_pct else THEME.STATUS_OFF_TRACK
                    };">{closure_pct:.1f}%</div>
                    <div style="color: {THEME.TEXT_MUTED}; font-size: 0.85rem;">
                        Target: {target_pct}% | Status: {'✅ On Track' if closure_pct >= target_pct else '⚠️ Off Track'}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        except (ValueError, TypeError):
            pass


def _render_frequency_rates(sheet) -> None:
    """Renders LTIFR, TRFR, and Near Miss Frequency Rate trends."""
    rate_kpis = [
        "Lost Time Injury frequency rate",
        "Total recordable frequency rate",
        "Near Miss Frequency Rate",
    ]
    
    cols_to_plot = []
    for kpi_name in rate_kpis:
        col = _find_hs_column(sheet, kpi_name)
        if col:
            cols_to_plot.append(col)
    
    if cols_to_plot:
        trend_df = _build_hs_trend_df(sheet, cols_to_plot)
        fig = render_line_chart(
            df=trend_df, x_col="Month", y_cols=cols_to_plot,
            title="Safety Frequency Rates", y_title="Rate per Million Hours",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_safety_training(sheet) -> None:
    """Renders safety training hours and worker involvement metrics."""
    training_hours_col = _find_hs_column(sheet, "Safety hours trained")
    involvement_col = _find_hs_column(sheet, "Safety observation worker involvement % [%]")
    
    cols_layout = st.columns(2)
    
    with cols_layout[0]:
        if training_hours_col:
            trend_df = _build_hs_trend_df(sheet, [training_hours_col])
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[training_hours_col],
                title="Monthly Safety Training Hours", y_title="Hours",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
            ytd = compute_ytd_summary(sheet.df_wide, training_hours_col, sheet.ytd_column)
            st.metric("YTD Training Hours", f"{ytd:,.0f}" if ytd else "N/A")
    
    with cols_layout[1]:
        if involvement_col:
            trend_df = _build_hs_trend_df(sheet, [involvement_col])
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[involvement_col],
                title="Worker Involvement in Safety Observations", y_title="%",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
            target_col = _find_hs_column(sheet, "Safety observation worker involvement % [%]")
            # Extract target from metadata if available
            meta = sheet.kpi_metadata.get(
                next((k for k, v in sheet.kpi_metadata.items() 
                      if v["full_column"] == involvement_col), None), {}
            )
            target = meta.get("target", 85.0)
            achievement, _, status = calculate_achievement(
                sheet.df_wide.iloc[0][involvement_col], target, lower_is_better=False
            )
            st.metric(
                "Current Involvement Rate",
                f"{sheet.df_wide.iloc[0][involvement_col]:.1f}%",
                delta=f"{achievement}% of Target ({status})"
            )


def _find_hs_column(sheet, partial_name: str) -> str | None:
    """Finds H&S column by partial name match."""
    for kpi_name, meta in sheet.kpi_metadata.items():
        if partial_name.lower() in kpi_name.lower():
            return meta["full_column"]
    return None


def _build_hs_trend_df(sheet, columns: list) -> pd.DataFrame:
    """Creates long-format trend dataframe for H&S charts."""
    rows = []
    for mc in sheet.month_columns:
        row = {"Month": mc}
        for col in columns:
            if col in sheet.df_wide.columns:
                val = sheet.df_wide.iloc[0][col]
                # Handle percentage strings
                if isinstance(val, str) and "%" in val:
                    try:
                        val = float(val.replace("%", ""))
                    except ValueError:
                        val = None
                row[col] = val
        rows.append(row)
    return pd.DataFrame(rows)
