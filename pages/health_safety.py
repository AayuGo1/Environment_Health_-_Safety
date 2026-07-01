"""
Health & Safety Performance Page Module
=========================================
Dedicated H&S analytics view featuring lagging vs leading indicator
separation, TRIR/LTIFR frequency rate trends, UA/UC observation
closure tracking, and safety training effectiveness analysis.
FIXED: Corrected data access pattern to use row_idx from kpi_metadata
instead of broken iloc[0] assumption. Matches Excel structure where
KPIs are ROWS and months are COLUMNS.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List

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
        st.error("❌ Health & Safety sheet not found in workbook")
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


def _render_lagging_indicators(sheet: Any) -> None:
    """Renders fatality, LTI, RWC, and first aid incident trends."""
    lagging_keywords = [
        "fatalities", "lost time injury", "restricted work case", 
        "first aid accident", "significant near miss", "offsite medical"
    ]
    
    cols_to_plot: List[str] = []
    labels: List[str] = []
    
    for kpi_name, meta in sheet.kpi_metadata.items():
        if any(kw in kpi_name.lower() for kw in lagging_keywords):
            cols_to_plot.append(meta["full_column"])
            labels.append(kpi_name[:30])
    
    if cols_to_plot:
        # Build trend df using first lagging KPI's row index as reference
        # Actually need separate rows per KPI - simplified for line chart
        # For multi-line, we need long format or multiple traces
        # Using simplified approach: plot each as separate series
        trend_dfs = []
        for col, label in zip(cols_to_plot, labels):
            row_idx = next(m["row_idx"] for m in sheet.kpi_metadata.values() if m["full_column"] == col)
            tdf = _build_hs_trend_df(sheet, [col], row_idx)
            tdf.columns = ["Month", label]
            trend_dfs.append(tdf.set_index("Month"))
        
        if trend_dfs:
            combined = pd.concat(trend_dfs, axis=1).reset_index()
            fig = render_line_chart(
                df=combined, x_col="Month", y_cols=labels,
                title="Lagging Indicator Trends", y_title="Count",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # YTD Summary Cards
    summary_kpis = ["Fatalities", "Lost Time Injury", "First Aid Accident", "Significant Near Miss"]
    summary_cols = st.columns(min(len(summary_kpis), 4))
    
    for idx, kpi_name in enumerate(summary_kpis):
        meta = _find_hs_metadata(sheet, kpi_name)
        if meta and idx < len(summary_cols):
            row_idx = meta["row_idx"]
            ytd = compute_ytd_summary(
                df_wide=sheet.df_wide,
                row_idx=row_idx,
                ytd_column=sheet.ytd_column,
                month_columns=sheet.month_columns
            )
            with summary_cols[idx]:
                st.metric(
                    label=kpi_name,
                    value=f"{int(ytd)}" if ytd else "0",
                    delta="YTD Total",
                    delta_color="normal"
                )


def _render_leading_indicators(sheet: Any) -> None:
    """Renders UA/UC observations, unsafe acts/conditions, and near miss trends."""
    leading_keywords = [
        "near miss", "ua/uc obsevations", "unsafe conditions", 
        "unsafe act", "number of different people"
    ]
    
    cols_to_plot: List[str] = []
    labels: List[str] = []
    
    for kpi_name, meta in sheet.kpi_metadata.items():
        if any(kw in kpi_name.lower() for kw in leading_keywords):
            cols_to_plot.append(meta["full_column"])
            labels.append(kpi_name[:30])
    
    if cols_to_plot:
        trend_dfs = []
        for col, label in zip(cols_to_plot, labels):
            row_idx = next(m["row_idx"] for m in sheet.kpi_metadata.values() if m["full_column"] == col)
            tdf = _build_hs_trend_df(sheet, [col], row_idx)
            tdf.columns = ["Month", label]
            trend_dfs.append(tdf.set_index("Month"))
        
        if trend_dfs:
            combined = pd.concat(trend_dfs, axis=1).reset_index()
            fig = render_line_chart(
                df=combined, x_col="Month", y_cols=labels,
                title="Leading Indicator Trends", y_title="Count",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # UA/UC Closure Rate Gauge
    closure_meta = _find_hs_metadata(sheet, "% of UA/UC Closure")
    if closure_meta:
        row_idx = closure_meta["row_idx"]
        latest_month = sheet.month_columns[-1] if sheet.month_columns else None
        
        if latest_month and latest_month in sheet.df_wide.columns:
            try:
                raw_val = sheet.df_wide.loc[sheet.df_wide.index[row_idx], latest_month]
                if isinstance(raw_val, str) and '%' in raw_val:
                    closure_pct = float(raw_val.replace('%', ''))
                else:
                    closure_pct = float(raw_val)
                
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
            except (ValueError, TypeError, KeyError, IndexError):
                pass


def _render_frequency_rates(sheet: Any) -> None:
    """Renders LTIFR, TRFR, and Near Miss Frequency Rate trends."""
    rate_keywords = [
        "lost time injury frequency rate", "total recordable frequency rate",
        "near miss frequency rate"
    ]
    
    cols_to_plot: List[str] = []
    labels: List[str] = []
    
    for kpi_name, meta in sheet.kpi_metadata.items():
        if any(kw in kpi_name.lower() for kw in rate_keywords):
            cols_to_plot.append(meta["full_column"])
            labels.append(kpi_name[:35])
    
    if cols_to_plot:
        trend_dfs = []
        for col, label in zip(cols_to_plot, labels):
            row_idx = next(m["row_idx"] for m in sheet.kpi_metadata.values() if m["full_column"] == col)
            tdf = _build_hs_trend_df(sheet, [col], row_idx)
            tdf.columns = ["Month", label]
            trend_dfs.append(tdf.set_index("Month"))
        
        if trend_dfs:
            combined = pd.concat(trend_dfs, axis=1).reset_index()
            fig = render_line_chart(
                df=combined, x_col="Month", y_cols=labels,
                title="Safety Frequency Rates", y_title="Rate per Million Hours",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_safety_training(sheet: Any) -> None:
    """Renders safety training hours and worker involvement metrics."""
    training_hours_meta = _find_hs_metadata(sheet, "Safety hours trained")
    involvement_meta = _find_hs_metadata(sheet, "Safety observation worker involvement %")
    
    cols_layout = st.columns(2)
    
    with cols_layout[0]:
        if training_hours_meta:
            row_idx = training_hours_meta["row_idx"]
            trend_df = _build_hs_trend_df(sheet, [training_hours_meta["full_column"]], row_idx)
            
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[training_hours_meta["full_column"]],
                title="Monthly Safety Training Hours", y_title="Hours",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
            ytd = compute_ytd_summary(
                df_wide=sheet.df_wide,
                row_idx=row_idx,
                ytd_column=sheet.ytd_column,
                month_columns=sheet.month_columns
            )
            st.metric("YTD Training Hours", f"{ytd:,.0f}" if ytd else "N/A")
    
    with cols_layout[1]:
        if involvement_meta:
            row_idx = involvement_meta["row_idx"]
            trend_df = _build_hs_trend_df(sheet, [involvement_meta["full_column"]], row_idx)
            
            fig = render_line_chart(
                df=trend_df, x_col="Month", y_cols=[involvement_meta["full_column"]],
                title="Worker Involvement in Safety Observations", y_title="%",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Get current value and calculate achievement
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
                    pass
            
            target = involvement_meta.get("target", 85.0)
            achievement, _, status = calculate_achievement(current_val, target, lower_is_better=False)
            
            st.metric(
                "Current Involvement Rate",
                f"{current_val:.1f}%" if current_val else "N/A",
                delta=f"{achievement}% of Target ({status})" if achievement else None
            )


def _find_hs_metadata(sheet: Any, partial_name: str) -> Optional[Dict]:
    """Finds H&S KPI metadata by partial name match."""
    if not hasattr(sheet, 'kpi_metadata'):
        return None
        
    for kpi_name, meta in sheet.kpi_metadata.items():
        if partial_name.lower() in kpi_name.lower():
            return meta
    return None


def _build_hs_trend_df(sheet: Any, columns: List[str], row_idx: int) -> pd.DataFrame:
    """
    Creates long-format trend dataframe for a SPECIFIC H&S KPI row.
    FIXED: Uses row_idx instead of iloc[0] to get correct KPI data.
    Handles percentage strings and NA values gracefully.
    
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
                    
                    # Handle NA values
                    if isinstance(val, str) and val.strip().upper() in ("NA", "N/A", "-"):
                        row[col] = None
                        continue
                    
                    # Handle percentage strings
                    if isinstance(val, str) and '%' in val:
                        val = float(val.replace('%', ''))
                    
                    row[col] = float(val)
                except (ValueError, TypeError, KeyError, IndexError):
                    row[col] = None
        rows.append(row)
    return pd.DataFrame(rows)
