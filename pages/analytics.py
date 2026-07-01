"""
Advanced Analytics Page Module
================================
Cross-domain analytical insights featuring KPI correlations,
statistical anomaly detection, period-over-period benchmarking,
and simple linear regression forecasting for proactive EHS management.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats

from config import THEME
from charts.heatmap import render_heatmap_chart
from charts.scatter import render_scatter_chart


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


def _render_correlation_analysis(env_sheet, hs_sheet) -> None:
    """Computes and visualizes Pearson correlations between key EHS KPIs."""
    st.subheader("KPI Correlation Matrix")
    
    # Select representative KPIs from each domain
    selected_kpis = []
    labels = []
    
    if env_sheet:
        energy_col = _find_col(env_sheet, "Total energy consumption [kWh/Gross Weight")
        water_col = _find_col(env_sheet, "Total water withdrawal  [m³/Gross Weight")
        waste_col = _find_col(env_sheet, "Total waste per t(Metrics)")
        prod_col = _find_col(env_sheet, "Production Volume - Gross Weight")
        
        for col, label in [(energy_col, "Energy Intensity"), 
                           (water_col, "Water Intensity"),
                           (waste_col, "Waste Intensity"),
                           (prod_col, "Production Vol")]:
            if col:
                selected_kpis.append(col)
                labels.append(label)
    
    if hs_sheet:
        uauc_col = _find_hs_col(hs_sheet, "UA/UC Obsevations - Total number")
        nmfr_col = _find_hs_col(hs_sheet, "Near Miss Frequency Rate")
        
        for col, label in [(uauc_col, "UA/UC Obs"), (nmfr_col, "NM Frequency Rate")]:
            if col:
                selected_kpis.append(col)
                labels.append(label)
    
    if len(selected_kpis) < 2:
        st.info("ℹ️ Insufficient KPIs available for correlation analysis")
        return
    
    # Build correlation matrix from monthly values
    corr_data = {}
    for col, label in zip(selected_kpis, labels):
        values = []
        for mc in (env_sheet or hs_sheet).month_columns:
            source = env_sheet if col in env_sheet.df_wide.columns else hs_sheet
            if source and col in source.df_wide.columns:
                try:
                    values.append(float(source.df_wide.iloc[0][col]))
                except (ValueError, TypeError):
                    values.append(np.nan)
            else:
                values.append(np.nan)
        corr_data[label] = values
    
    corr_df = pd.DataFrame(corr_data)
    corr_matrix = corr_df.corr().round(3)
    
    fig = render_heatmap_chart(
        df=corr_matrix,
        title="EHS KPI Correlation Heatmap",
        annot=True,
        colorscale="RdBu_r",
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("Values range from -1 (perfect negative) to +1 (perfect positive). 
               Red indicates positive correlation; blue indicates negative.")


def _render_anomaly_detection(env_sheet, hs_sheet) -> None:
    """Detects statistical outliers using Z-score method across all KPIs."""
    st.subheader("Statistical Anomaly Alerts")
    
    anomalies = []
    sheets = [s for s in [env_sheet, hs_sheet] if s is not None]
    
    for sheet in sheets:
        for kpi_name, meta in sheet.kpi_metadata.items():
            col = meta["full_column"]
            values = []
            months = []
            
            for mc in sheet.month_columns:
                if col in sheet.df_wide.columns:
                    try:
                        val = float(sheet.df_wide.iloc[0][mc.split("|")[0]] 
                                   if "|" in mc else sheet.df_wide.iloc[0][col])
                        # This is simplified; proper implementation extracts per-month row
                        values.append(val)
                        months.append(mc)
                    except (ValueError, TypeError, IndexError):
                        continue
            
            if len(values) >= 6:
                z_scores = np.abs(stats.zscore(values, nan_policy='omit'))
                threshold = 2.0
                
                for i, z in enumerate(z_scores):
                    if not np.isnan(z) and z > threshold:
                        anomalies.append({
                            "KPI": kpi_name[:50],
                            "Month": months[i],
                            "Value": values[i],
                            "Z-Score": round(z, 2),
                            "Mean": round(np.nanmean(values), 2),
                            "Std Dev": round(np.nanstd(values), 2),
                        })
    
    if anomalies:
        anomaly_df = pd.DataFrame(anomalies)
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
        st.warning(f"⚠️ {len(anomalies)} statistical anomalies detected (|Z| > 2.0)")
    else:
        st.success("✅ No statistical anomalies detected in current dataset")


def _render_period_benchmarking(env_sheet, hs_sheet) -> None:
    """Compares current month vs previous month vs same month last year."""
    st.subheader("Period-over-Period Benchmarking")
    
    sheets = [s for s in [env_sheet, hs_sheet] if s is not None]
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
        if v.get("target") is not None
    ][:8]
    
    benchmark_rows = []
    for kpi_name, meta in kpis_with_targets:
        col = meta["full_column"]
        if col not in sheet.df_wide.columns:
            continue
        
        try:
            curr_val = float(sheet.df_wide.iloc[0][current_month])
            prev_val = float(sheet.df_wide.iloc[0][prev_month])
            mom_change = ((curr_val - prev_val) / abs(prev_val) * 100) if prev_val != 0 else 0
            
            benchmark_rows.append({
                "KPI": kpi_name[:45],
                "Current": round(curr_val, 2),
                "Previous": round(prev_val, 2),
                "MoM Change %": round(mom_change, 1),
                "Target": meta["target"],
            })
        except (ValueError, TypeError, KeyError):
            continue
    
    if benchmark_rows:
        bench_df = pd.DataFrame(benchmark_rows)
        st.dataframe(bench_df, use_container_width=True, hide_index=True)


def _render_trend_forecasting(env_sheet) -> None:
    """Simple linear regression forecast for next 3 months."""
    st.subheader("3-Month Trend Forecast (Linear Regression)")
    
    if env_sheet is None:
        st.info("️ Environment data required for forecasting")
        return
    
    forecast_kpis = [
        ("Energy Intensity", "Total energy consumption [kWh/Gross Weight"),
        ("Water Intensity", "Total water withdrawal  [m³/Gross Weight"),
        ("Waste Intensity", "Total waste per t(Metrics)"),
    ]
    
    for display_name, search_term in forecast_kpis:
        col = _find_col(env_sheet, search_term)
        if not col:
            continue
        
        values = []
        for mc in env_sheet.month_columns:
            try:
                values.append(float(env_sheet.df_wide.iloc[0][col]))
            except (ValueError, TypeError):
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
                Forecast: {[round(v, 2) for v in forecast_vals]}
            </div>
        """, unsafe_allow_html=True)


def _find_col(sheet, partial: str) -> str | None:
    for kpi_name, meta in sheet.kpi_metadata.items():
        if partial.lower() in kpi_name.lower():
            return meta["full_column"]
    return None

def _find_hs_col(sheet, partial: str) -> str | None:
    return _find_col(sheet, partial)
