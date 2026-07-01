"""
Line Chart Module
==================
Professional multi-line trend visualization with dynamic styling,
target reference lines, and intelligent legend management.
Adapts colors and formatting based on KPI category metadata.
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional, Dict
import pandas as pd

from config import THEME
from constants import KPICategory


def render_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    title: str,
    y_title: str = "Value",
    height: int = 400,
    show_target: bool = False,
    target_value: Optional[float] = None,
    kpi_metadata: Optional[Dict] = None,
) -> go.Figure:
    """
    Creates a professional line chart with optional target reference.
    
    Args:
        df: Dataframe with month columns as x-axis values.
        x_col: Column name for x-axis (typically 'Month').
        y_cols: List of column names to plot as separate lines.
        title: Chart title displayed above the plot.
        y_title: Y-axis label text.
        height: Chart height in pixels.
        show_target: Whether to display horizontal target line.
        target_value: Numeric value for target reference line.
        kpi_metadata: Dictionary mapping KPI names to {unit, lower_is_better}.
        
    Returns:
        Plotly Figure object ready for st.plotly_chart().
    """
    fig = px.line(
        df, x=x_col, y=y_cols,
        title=title,
        markers=True,
        template="plotly_white",
        height=height,
        color_discrete_map=_get_color_mapping(y_cols, kpi_metadata),
    )
    
    # Add target reference line if specified
    if show_target and target_value is not None:
        fig.add_hline(
            y=target_value,
            line_dash="dash",
            line_color=THEME.TEXT_WARNING,
            annotation_text=f"Target: {target_value:,.2f}",
            annotation_position="top right",
            opacity=0.7,
        )
    
    # Professional layout configuration
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=THEME.CARD_BORDER,
            borderwidth=1,
        ),
        plot_bgcolor="rgba(240,242,245,0.5)",
        hovermode="x unified",
        yaxis_title=y_title,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    
    # Style traces based on KPI directionality
    for trace in fig.data:
        meta = kpi_metadata.get(trace.name, {}) if kpi_metadata else {}
        if meta.get("lower_is_better"):
            trace.line.color = THEME.CHART_SECONDARY  # Teal for intensity metrics
        else:
            trace.line.color = THEME.CHART_PRIMARY   # Blue for production/volume
    
    return fig


def _get_color_mapping(
    y_cols: List[str], 
    metadata: Optional[Dict]
) -> Dict[str, str]:
    """Maps KPI names to theme-consistent colors."""
    mapping = {}
    palette = [
        THEME.CHART_PRIMARY,
        THEME.CHART_SECONDARY,
        THEME.CHART_ACCENT_1,
        THEME.CHART_ACCENT_2,
    ]
    
    for i, col in enumerate(y_cols):
        if metadata and col in metadata:
            if metadata[col].get("lower_is_better"):
                mapping[col] = THEME.CHART_SECONDARY
            else:
                mapping[col] = THEME.CHART_PRIMARY
        else:
            mapping[col] = palette[i % len(palette)]
    
    return mapping
