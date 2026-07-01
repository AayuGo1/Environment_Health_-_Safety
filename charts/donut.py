"""
Donut Chart Module
===================
Professional composition visualization with centered hole,
percentage+label annotations, and vertical legend positioning.
Optimized for waste streams, energy sources, and category splits.
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional
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
    fig = px.pie(
        df,
        values=values_col,
        names=names_col,
        title=title,
        hole=hole_size,
        template="plotly_white",
        height=height,
        color_discrete_sequence=[
            THEME.CHART_PRIMARY,
            THEME.CHART_SECONDARY,
            THEME.CHART_ACCENT_1,
            THEME.CHART_ACCENT_2,
            THEME.TEXT_WARNING,
            THEME.TEXT_DANGER,
        ],
    )
    
    # Configure segment labels
    text_info = "percent+label" if show_percentages else "label"
    fig.update_traces(
        textposition="inside",
        textinfo=text_info,
        insidetextfont=dict(size=11, color="white"),
        marker=dict(line=dict(color=THEME.CARD_BG, width=2)),
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
                font=dict(size=14, color=THEME.TEXT_DARK),
                showarrow=False,
            )
        ] if hole_size > 0.4 else [],
    )
    
    return fig
