"""
Analytics Calculations Module
===============================
Core business logic for KPI evaluation, trend analysis, and 
performance scoring. All calculations are vectorized where possible
and include comprehensive edge-case handling.
"""

from typing import Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd

from constants import KPI_RULES, EXCEL


def calculate_achievement(
    actual: Optional[float],
    target: Optional[float],
    lower_is_better: bool = False
) -> Tuple[Optional[float], Optional[float], str]:
    """
    Calculates achievement percentage, variance, and status indicator.
    
    Args:
        actual: Current period actual value
        target: Target value for comparison
        lower_is_better: True if lower values indicate better performance
        
    Returns:
        Tuple of (achievement_pct, variance, status_string)
    """
    if actual is None or target is None or pd.isna(target) or target == 0:
        return None, None, "ℹ️ No Target"
    
    if lower_is_better:
        # For intensity/incident metrics: achieving target means being at or below it
        achievement = (target / actual * 100) if actual > 0 else 100.0
        variance = target - actual  # Positive = under target (good)
        status = "✅ On Track" if actual <= target else "⚠️ Off Track"
    else:
        # For production/recycling metrics: achieving target means meeting/exceeding it
        achievement = (actual / target * 100) if target > 0 else 0.0
        variance = actual - target  # Positive = over target (good)
        status = "✅ On Track" if actual >= target else "⚠️ Off Track"
    
    return round(achievement, 1), round(variance, 2), status


def calculate_mom_trend(
    current: Optional[float],
    previous: Optional[float]
) -> Tuple[Optional[float], str]:
    """Calculates month-over-month percentage change and direction."""
    if current is None or previous is None or pd.isna(previous) or previous == 0:
        return None, "neutral"
    
    pct_change = ((current - previous) / abs(previous)) * 100
    direction = "up" if pct_change > 0 else ("down" if pct_change < 0 else "flat")
    return round(pct_change, 1), direction


def extract_sparkline_data(
    df_wide: pd.DataFrame,
    kpi_column: str,
    month_columns: List[str],
    lookback: int = KPI_RULES.SPARKLINE_MONTHS
) -> list:
    """Extracts last N months of data for sparkline rendering."""
    relevant_months = month_columns[-lookback:]
    values = []
    for mc in relevant_months:
        if mc in df_wide.columns:
            val = df_wide.iloc[0].get(mc)
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                values.append(np.nan)
    return values


def compute_ytd_summary(
    df_wide: pd.DataFrame,
    kpi_column: str,
    ytd_column: Optional[str]
) -> Optional[float]:
    """Computes or retrieves YTD value for a KPI."""
    # Prefer explicit YTD column if available
    if ytd_column and ytd_column in df_wide.columns:
        val = df_wide.iloc[0].get(ytd_column)
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    
    # Fallback: sum all month columns for this KPI
    month_pattern = EXCEL.MONTH_PATTERN
    month_cols = [
        c for c in df_wide.columns 
        if month_pattern.search(c.split(EXCEL.HEADER_SEPARATOR)[-1].strip())
    ]
    
    total = 0.0
    count = 0
    for mc in month_cols:
        if mc in df_wide.columns:
            val = df_wide.iloc[0].get(mc)
            try:
                total += float(val)
                count += 1
            except (ValueError, TypeError):
                continue
    
    return round(total, 2) if count > 0 else None


def determine_display_precision(kpi_name: str, unit: str) -> int:
    """Returns appropriate decimal precision based on KPI type."""
    name_lower = kpi_name.lower()
    
    if any(kw in name_lower for kw in ["rate", "%", "involvement", "closure"]):
        return KPI_RULES.PRECISION_PERCENTAGE
    elif any(kw in name_lower for kw in ["intensity", "per t", "/gross"]):
        return KPI_RULES.PRECISION_INTENSITY
    elif any(kw in name_lower for kw in ["volume", "weight", "production"]):
        return KPI_RULES.PRECISION_VOLUME
    elif any(kw in name_lower for kw in ["fatality", "injury", "accident", "miss"]):
        return KPI_RULES.PRECISION_COUNT
    
    # Default based on unit
    if "%" in unit:
        return KPI_RULES.PRECISION_PERCENTAGE
    elif "/" in unit:
        return KPI_RULES.PRECISION_INTENSITY
    
    return KPI_RULES.PRECISION_VOLUME
