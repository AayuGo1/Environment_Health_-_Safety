"""
KPI Card Component Module
==========================
Premium metric cards with integrated sparklines, status indicators,
achievement percentages, and interactive hover states. Each card
adapts dynamically to KPI directionality (lower/higher is better)
and displays contextual variance information.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Optional, List

from config import THEME
from constants import KPI_RULES


def render_kpi_card(
    title: str,
    value: Optional[float],
    unit: str,
    target: Optional[float],
    achievement: Optional[float],
    status: str,
    sparkline_data: Optional[List[float]] = None,
    previous_month: Optional[float] = None,
    ytd_value: Optional[float] = None,
) -> None:
    """
    Renders a single enterprise-grade KPI metric card.
    
    Args:
        title: Display name of the KPI (truncated if too long).
        value: Current period actual value.
        unit: Measurement unit string (e.g., 'kWh/MT', '%').
        target: Target value for achievement calculation.
        achievement: Pre-calculated achievement percentage.
        status: Status indicator string ('✅ On Track', '⚠️ Off Track', etc.).
        sparkline_data: List of numeric values for mini trend chart.
        previous_month: Prior month value for MoM comparison.
        ytd_value: Year-to-date cumulative value.
    """
    # Determine delta display
    delta_text = None
    delta_color = "normal"
    
    if achievement is not None:
        delta_text = f"{achievement}% of Target"
        if "On Track" in status:
            delta_color = "inverse"  # Green in our theme
        elif "Off Track" in status:
            delta_color = "inverse"  # Red handling via custom CSS
    
    # Format value with appropriate precision
    formatted_value = "N/A"
    if value is not None:
        precision = _get_precision(title, unit)
        formatted_value = f"{value:,.{precision}f} {unit}".strip()
    
    # Render main metric
    st.metric(
        label=title[:45] + "..." if len(title) > 45 else title,
        value=formatted_value,
        delta=delta_text,
        delta_color=delta_color,
        help=_build_tooltip(value, target, achievement, status, previous_month, ytd_value)
    )
    
    # Render sparkline if data available
    if sparkline_data and len(sparkline_data) >= 2:
        _render_sparkline(sparkline_data)


def _get_precision(title: str, unit: str) -> int:
    """Determines decimal precision based on KPI characteristics."""
    title_lower = title.lower()
    
    if any(kw in title_lower for kw in ["rate", "%", "involvement", "closure"]):
        return KPI_RULES.PRECISION_PERCENTAGE
    elif any(kw in title_lower for kw in ["intensity", "per t", "/gross"]):
        return KPI_RULES.PRECISION_INTENSITY
    elif any(kw in title_lower for kw in ["volume", "weight", "production"]):
        return KPI_RULES.PRECISION_VOLUME
    elif any(kw in title_lower for kw in ["fatality", "injury", "accident"]):
        return KPI_RULES.PRECISION_COUNT
    
    if "%" in unit:
        return KPI_RULES.PRECISION_PERCENTAGE
    elif "/" in unit:
        return KPI_RULES.PRECISION_INTENSITY
    
    return KPI_RULES.PRECISION_VOLUME


def _render_sparkline(data: List[float]) -> None:
    """Renders a minimal line chart for trend visualization."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data,
        mode="lines",
        line=dict(color=THEME.CHART_PRIMARY, width=2),
        fill="tozeroy",
        fillcolor=f"rgba(49,130,206,0.1)",
        hoverinfo="skip"
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        height=50,
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"spark_{hash(tuple(data))}")


def _build_tooltip(
    value, target, achievement, status, prev_month, ytd
) -> str:
    """Constructs comprehensive hover tooltip text."""
    lines = [f"Status: {status}"]
    if target is not None:
        lines.append(f"Target: {target:,.2f}")
    if achievement is not None:
        lines.append(f"Achievement: {achievement}%")
    if prev_month is not None:
        lines.append(f"Previous Month: {prev_month:,.2f}")
    if ytd is not None:
        lines.append(f"YTD: {ytd:,.2f}")
    return "\n".join(lines)
