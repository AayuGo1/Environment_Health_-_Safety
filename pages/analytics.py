"""
Advanced Analytics Page Module
================================
Cross-domain analytical insights featuring KPI correlations,
statistical anomaly detection, period-over-period benchmarking,
and simple linear regression forecasting for proactive EHS management.
FIXED: Syntax errors, indentation, broken imports, and row-index data access.
Matches Excel structure where KPIs are ROWS and months are COLUMNS.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats

from config import THEME
from constants import KPICategory, EXCEL, KPI_RULES


def render_analytics_page(parsed_data: Dict[str, Any]) -> None:
    """
    Renders the complete Advanced Analytics page.
    
    Args:
        parsed_data: Dictionary containing ParsedSheet objects.
    """
    env_sheet = parsed_data.get("Environment")
    hs_sheet = parsed_data.get("Health & Safety")
    
    if env_sheet is None and hs_sheet is None:
        st.error("❌ No data available for analytics")
        return

    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h2 style="color: {THEME.TEXT_LIGHT}; font-size: 1.8rem;">📈 Advanced Analytics</h2>
            <p style="color: {THEME.TEXT_MUTED}; font-size: 0.95rem;">
                Correlations, anomalies, benchmarks, and forecasts
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_corr, tab_anomaly, tab_benchmark, tab_forecast = st.tabs([
        "KPI Correlations", "Anomaly Detection", "Period Benchmarking", "Trend Forecast"
    ])

    with tab_corr:
        _render_correlation_analysis(env_sheet, hs_sheet)
    
    with tab_anomaly:
        _render_anomaly_detection(env_sheet, hs_sheet)
    
    with tab_benchmark:
        _render_period_benchmarking(env_sheet, hs_sheet)
    
    with tab_forecast:
        _render_trend_forecasting(env_sheet)


def _render_correlation_analysis(env_sheet: Optional[Any], hs_sheet: Optional[Any]) -> None:
    """Computes and visualizes Pearson correlations between key EHS KPIs."""
    st.subheader("KPI Correlation Matrix")
    
    selected_kpis: List[Tuple[str, str, int]] = []  # (col_name, sheet_type, row_idx)
    labels: List[str] = []
    
    # Select representative KPIs from Environment sheet
    if env_sheet and hasattr(env_sheet, 'kpi_metadata'):
        env_searches = [
            ("Total energy consumption [kWh/Gross Weight", "Energy Intensity"),
            ("Total water withdrawal  [m³/Gross Weight", "Water Intensity"),
            ("Total waste per t(Metrics)", "Waste Intensity"),
            ("Production Volume - Gross Weight", "Production Vol")
        ]
        
        for search_term, label in env_searches:
            meta = _find_kpi_metadata(env_sheet, search_term)
            if meta:
                selected_kpis.append((meta["full_column"], "env", meta["row_idx"]))
                labels.append(label)
    
    # Add H&S KPIs if available
    if hs_sheet and hasattr(hs_sheet, 'kpi_metadata'):
        hs_searches = [
            ("UA/UC Obsevations - Total number", "UA/UC Obs"),
            ("Near Miss Frequency Rate", "NM Frequency Rate")
        ]
        
        for search_term, label in hs_searches:
            meta = _find_kpi_metadata(hs_sheet, search_term)
            if meta:
                selected_kpis.append((meta["full_column"], "hs", meta["row_idx"]))
                labels.append(label)
    
    if len(selected_kpis) < 2:
        st.info("ℹ️ Insufficient KPIs available for correlation analysis")
        return
    
    # Build correlation matrix from monthly values using row indices
    corr_data: Dict[str, List[float]] = {}
    
    for col, sheet_type, row_idx in selected_kpis:
        source = env_sheet if sheet_type == "env" else hs_sheet
        values: List[float] = []
        
        if source:
            for mc in source.month_columns:
                if col in source.df_wide.columns:
                    try:
                        raw_val = source.df_wide.loc[source.df_wide.index[row_idx], mc]
                        if isinstance(raw_val, str) and '%' in raw_val:
                            val = float(raw_val.replace('%', ''))
                        else:
                            val = float(raw_val)
                        values.append(val)
                    except (ValueError, TypeError, KeyError, IndexError):
                        values.append(np.nan)
                else:
                    values.append(np.nan)
        
        corr_data[labels[selected_kpis.index((col, sheet_type, row_idx))]] = values
    
    corr_df = pd.DataFrame(corr_data).dropna(axis=1, how='all')
    if corr_df.shape[1] < 2:
        st.info("Insufficient valid data points for correlation")
        return
        
    corr_matrix = corr_df.corr().round(3)
    
    # Safe heatmap rendering with fallback
    try:
        from charts.heatmap import render_heatmap_chart
        fig = render_heatmap_chart(
            df=corr_matrix,
            title="EHS KPI Correlation Heatmap",
            annot=True,
            colorscale="RdBu_r",
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.warning("Heatmap chart module not found. Showing raw correlation table.")
        st.dataframe(corr_matrix, use_container_width=True)
    
    st.caption(
        "Values range from -1 (perfect negative) to +1 (perfect positive). "
        "Red indicates positive correlation; blue indicates negative."
    )


def _render_anomaly_detection(env_sheet: Optional[Any], hs_sheet: Optional[Any]) -> None:
    """Detects statistical outliers using Z-score method across all KPIs."""
    st.subheader("Statistical Anomaly Alerts")
    
    anomalies: List[Dict[str, Any]] = []
    sheets = [s for s in [env_sheet, hs_sheet] if s is not None and hasattr(s, 'kpi_metadata')]
    
    for sheet in sheets:
        for kpi_name, meta in sheet.kpi_metadata.items():
            col = meta["full_column"]
            row_idx = meta.get("row_idx")
            
            if row_idx is None or col not in sheet.df_wide.columns:
                continue
            
            values: List[float] = []
            months: List[str] = []
            
            for mc in sheet.month_columns:
                try:
                    raw_val = sheet.df_wide.loc[sheet.df_wide.index[row_idx], mc]
                    if isinstance(raw_val, str) and '%' in raw_val:
                        val = float(raw_val.replace('%', ''))
                    else:
                        val = float(raw_val)
                    
                    if not np.isnan(val):
                        values.append(val)
                        months.append(mc)
                except (ValueError, TypeError, KeyError, IndexError):
                    continue
            
            if len(values) >= 6:
                z_scores = np.abs(stats.zscore(values, nan_policy='omit'))
                threshold = 2.0
                
                for i, z in enumerate(z_scores):
                    if not np.isnan(z) and z > threshold:
                        anomalies.append({
                            "KPI": kpi_name[:50],
                            "Month": months[i],
                            "Value": round(values[i], 2),
                            "Z-Score": round(float(z), 2),
                            "Mean": round(float(np.nanmean(values)), 2),
                            "Std Dev": round(float(np.nanstd(values)), 2),
                        })
    
    if anomalies:
        anomaly_df = pd.DataFrame(anomalies)
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
        st.warning(f"⚠️ {len(anomalies)} statistical anomalies detected (|Z| > 2.0)")
    else:
        st.success("✅ No statistical anomalies detected in current dataset")


def _render_period_benchmarking(env_sheet: Optional[Any], hs_sheet: Optional[Any]) -> None:
    """Compares current month vs previous month for top KPIs."""
    st.subheader("Period-over-Period Benchmarking")
    
    sheets = [s for s in [env_sheet, hs_sheet] if s is not None and hasattr(s, 'kpi_metadata')]
    if not sheets:
        return
    
    sheet = sheets[0]
    months = sheet.month_columns
    
    if len(months) < 2:
        st.info("ℹ️ Insufficient months for benchmarking")
        return
    
    current_month = months[-1]
    prev_month = months[-2]
    
    # Select top 8 KPIs with targets for comparison
    kpis_with_targets = [
        (k, v) for k, v in sheet.kpi_metadata.items() 
        if v.get("target") is not None and v.get("row_idx") is not None
    ][:8]
    
    benchmark_rows: List[Dict[str, Any]] = []
    for kpi_name, meta in kpis_with_targets:
        col = meta["full_column"]
        row_idx = meta["row_idx"]
        
        if col not in sheet.df_wide.columns:
            continue
        
        try:
            curr_raw = sheet.df_wide.loc[sheet.df_wide.index[row_idx], current_month]
            prev_raw = sheet.df_wide.loc[sheet.df_wide.index[row_idx], prev_month]
            
            # Handle percentages
            if isinstance(curr_raw, str) and '%' in curr_raw:
                curr_val = float(curr_raw.replace('%', ''))
            else:
                curr_val = float(curr_raw)
                
            if isinstance(prev_raw, str) and '%' in prev_raw:
                prev_val = float(prev_raw.replace('%', ''))
            else:
                prev_val = float(prev_raw)
            
            mom_change = ((curr_val - prev_val) / abs(prev_val) * 100) if prev_val != 0 else 0
            
            benchmark_rows.append({
                "KPI": kpi_name[:45],
                "Current": round(curr_val, 2),
                "Previous": round(prev_val, 2),
                "MoM Change %": round(mom_change, 1),
                "Target": meta["target"],
            })
        except (ValueError, TypeError, KeyError, IndexError):
            continue
    
    if benchmark_rows:
        bench_df = pd.DataFrame(benchmark_rows)
        st.dataframe(bench_df, use_container_width=True, hide_index=True)
    else:
        st.info("No comparable KPI data found for benchmarking")


def _render_trend_forecasting(env_sheet: Optional[Any]) -> None:
    """Simple linear regression forecast for next 3 months."""
    st.subheader("3-Month Trend Forecast (Linear Regression)")
    
    if env_sheet is None or not hasattr(env_sheet, 'kpi_metadata'):
        st.info("ℹ️ Environment data required for forecasting")
        return
    
    forecast_kpis = [
        ("Energy Intensity", "Total energy consumption [kWh/Gross Weight"),
        ("Water Intensity", "Total water withdrawal  [m³/Gross Weight"),
        ("Waste Intensity", "Total waste per t(Metrics)"),
    ]
    
    for display_name, search_term in forecast_kpis:
        meta = _find_kpi_metadata(env_sheet, search_term)
        if not meta:
            continue
        
        row_idx = meta.get("row_idx")
        col = meta["full_column"]
        
        if row_idx is None or col not in env_sheet.df_wide.columns:
            continue
        
        values: List[float] = []
        for mc in env_sheet.month_columns:
            try:
                raw_val = env_sheet.df_wide.loc[env_sheet.df_wide.index[row_idx], mc]
                if isinstance(raw_val, str) and '%' in raw_val:
                    values.append(float(raw_val.replace('%', '')))
                else:
                    values.append(float(raw_val))
            except (ValueError, TypeError, KeyError, IndexError):
                values.append(np.nan)
        
        valid_values = [v for v in values if not np.isnan(v)]
        if len(valid_values) < 6:
            continue
        
        x = np.arange(len(valid_values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, valid_values)
        
        future_x = np.arange(len(valid_values), len(valid_values) + 3)
        forecast_vals = slope * future_x + intercept
        
        st.markdown(f"""
            <div style="padding: 1rem; background: {THEME.CARD_BG}; 
                        border-radius: 8px; margin-bottom: 0.5rem;">
                <strong>{display_name}</strong><br/>
                Slope: {slope:.3f}/month | R²: {r_value**2:.3f}<br/>
                Forecast: {[round(float(v), 2) for v in forecast_vals]}
            </div>
        """, unsafe_allow_html=True)


def _find_kpi_metadata(sheet: Any, partial: str) -> Optional[Dict]:
    """Finds KPI metadata by partial name match."""
    if not hasattr(sheet, 'kpi_metadata'):
        return None
    for kpi_name, meta in sheet.kpi_metadata.items():
        if partial.lower() in kpi_name.lower():
            return meta
    return None
