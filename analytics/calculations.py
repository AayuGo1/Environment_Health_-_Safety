"""
Analytics Calculations Module
===============================
Core business logic for KPI evaluation, trend analysis, and 
performance scoring. All calculations use row-index-based data access
to match Excel structure where KPIs are ROWS and months are COLUMNS.
Includes comprehensive edge-case handling for percentages, NA values,
and type conversions.
"""

from typing import Optional, Tuple, Dict, Any, List
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
        actual: Current period actual value (must be numeric).
        target: Target value for comparison (must be numeric).
        lower_is_better: True if lower values indicate better performance.
        
    Returns:
        Tuple of (achievement_pct, variance, status_string).
    """
    if actual is None or target is None or pd.isna(target) or target == 0:
        return None, None, "ℹ️ No Target"
    
    # Ensure numeric types
    try:
        actual = float(actual)
        target = float(target)
    except (ValueError, TypeError):
        return None, None, "ℹ️ Invalid Data"
    
    if lower_is_better:
        # For intensity/incident metrics: achieving target means being at or below it
        achievement = (target / actual * 100) if actual > 0 else 100.0
        variance = target - actual  # Positive = under target (good)
        status = "✅ On Track" if actual <= target else "️ Off Track"
    else:
        # For production/recycling metrics: achieving target means meeting/exceeding it
        achievement = (actual / target * 100) if target > 0 else 0.0
        variance = actual - target  # Positive = over target (good)
        status = "✅ On Track" if actual >= target else "️ Off Track"
    
    return round(achievement, 1), round(variance, 2), status


def calculate_mom_trend(
    current: Optional[float],
    previous: Optional[float]
) -> Tuple[Optional[float], str]:
    """Calculates month-over-month percentage change and direction."""
    if current is None or previous is None:
        return None, "neutral"
    
    try:
        current = float(current)
        previous = float(previous)
    except (ValueError, TypeError):
        return None, "neutral"
    
    if pd.isna(previous) or previous == 0:
        return None, "neutral"
    
    pct_change = ((current - previous) / abs(previous)) * 100
    direction = "up" if pct_change > 0 else ("down" if pct_change < 0 else "flat")
    return round(pct_change, 1), direction


def extract_sparkline_data(
    df_wide: pd.DataFrame,
    row_idx: int,
    month_columns: List[str],
    lookback: int = KPI_RULES.SPARKLINE_MONTHS
) -> List[float]:
    """
    Extracts last N months of data for sparkline rendering.
    FIXED: Uses row_idx to get correct KPI row instead of iloc[0].
    
    Args:
        df_wide: Wide-format DataFrame (Rows=KPIs, Cols=Months).
        row_idx: Integer index of the KPI row to extract.
        month_columns: List of detected month column names.
        lookback: Number of recent months to include.
        
    Returns:
        List of numeric values for sparkline plotting.
    """
    relevant_months = month_columns[-lookback:]
    values: List[float] = []
    
    for mc in relevant_months:
        if mc in df_wide.columns:
            try:
                val = df_wide.loc[df_wide.index[row_idx], mc]
                # Handle percentage strings
                if isinstance(val, str) and '%' in val:
                    val = float(val.replace('%', ''))
                values.append(float(val))
            except (ValueError, TypeError, KeyError, IndexError):
                values.append(np.nan)
        else:
            values.append(np.nan)
            
    return values


def compute_ytd_summary(
    df_wide: pd.DataFrame,
    row_idx: int,
    ytd_column: Optional[str],
    month_columns: List[str]
) -> Optional[float]:
    """
    Computes or retrieves YTD value for a specific KPI row.
    FIXED: Uses row_idx for correct data access.
    
    Args:
        df_wide: Wide-format DataFrame.
        row_idx: Integer index of the KPI row.
        ytd_column: Name of explicit YTD column if available.
        month_columns: List of month column names for summation fallback.
        
    Returns:
        Numeric YTD value or None.
    """
    # Prefer explicit YTD column if available
    if ytd_column and ytd_column in df_wide.columns:
        try:
            val = df_wide.loc[df_wide.index[row_idx], ytd_column]
            if isinstance(val, str) and '%' in val:
                return float(val.replace('%', ''))
            return float(val)
        except (ValueError, TypeError, KeyError, IndexError):
            pass
    
    # Fallback: sum all month columns for this specific row
    total = 0.0
    count = 0
    for mc in month_columns:
        if mc in df_wide.columns:
            try:
                val = df_wide.loc[df_wide.index[row_idx], mc]
                if isinstance(val, str) and '%' in val:
                    val = float(val.replace('%', ''))
                total += float(val)
                count += 1
            except (ValueError, TypeError, KeyError, IndexError):
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
