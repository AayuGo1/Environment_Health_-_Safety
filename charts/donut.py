"""
Donut Chart Module
===================
Professional composition visualization with centered hole,
percentage+label annotations, and vertical legend positioning.
Optimized for waste streams, energy sources, and category splits.
FIXED: Corrected theme references and added robust empty data handling.
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import pandas as pd

from config import THEME


def render_donut_chart(
    df: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str,
    height: int = 350,
    hole_size: float = 0.6,
    show_percentages: bool = True,
) -> go.Figure:
    """
    Creates a professional donut chart for composition analysis.
    
    Args:
        df: Dataframe containing category and value columns.
        values_col: Column name with numeric values to visualize.
        names_col: Column name with category labels.
        title: Chart title displayed above the plot.
        height: Chart height in pixels.
        hole_size: Ratio of center hole to total radius (0-1).
        show_percentages: Whether to display % inside segments.
        
    Returns:
        Plotly Figure object ready for st.plotly_chart().
    """
    # Validate inputs
    if df.empty or values_col not in df.columns or names_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        fig.update_layout(height=height)
        return fig
    
    # Clamp hole size to valid range
    safe_hole = max(0.0, min(1.0, hole_size))
    
    # Filter out zero/negative values
    plot_df = df[df[values_col] > 0].copy()
    if plot_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="All values are zero", showarrow=False)
        fig.update_layout(height=height)
        return fig
    
    # Define enterprise color sequence
    color_seq = [
        THEME.CHART_PRIMARY,      # Blue
        THEME.CHART_SECONDARY,    # Teal
        THEME.CHART_ACCENT_1,     # Purple
        THEME.CHART_ACCENT_2,     # Gold
        THEME.STATUS_OFF_TRACK,   # Orange/Red for warnings
        "#718096",                # Grey for misc
    ]
    
    fig = px.pie(
        plot_df,
        values=values_col,
        names=names_col,
        title=title,
        hole=safe_hole,
        template="plotly_white",
        height=height,
        color_discrete_sequence=color_seq,
    )
    
    # Configure segment labels
    text_info = "percent+label" if show_percentages else "label"
    fig.update_traces(
        textposition="inside",
        textinfo=text_info,
        insidetextfont=dict(size=11, color="white"),
        marker=dict(line=dict(color=THEME.CARD_BG, width=2)),
        hovertemplate="<b>%{label}</b><br>%{value:,.1f} (%{percent})<extra></extra>",
    )
    
    # Professional legend positioning
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=THEME.CARD_BORDER,
            borderwidth=1,
        ),
        margin=dict(l=20, r=120, t=60, b=20),
        annotations=[
            dict(
                text="Total",
                x=0.5, y=0.5,
                font=dict(size=14, color=THEME.TEXT_DARK, family="Inter, sans-serif"),
                showarrow=False,
            )
        ] if safe_hole > 0.3 else [],
    )
    
    return fig
