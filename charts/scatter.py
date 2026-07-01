"""
Scatter Plot Chart Module
==========================
Professional scatter plot visualization for bivariate EHS analysis.
Returns valid plotly.graph_objects.Figure objects compatible with
st.plotly_chart(use_container_width=True).
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List
import pandas as pd

from config import THEME


def render_scatter_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "Scatter Plot",
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    hover_cols: Optional[List[str]] = None,
    height: int = 500,
    trendline: bool = False,
) -> go.Figure:
    """
    Creates a professional scatter plot for bivariate analysis.

    Args:
        df: DataFrame containing the data to visualize.
        x_col: Column name for x-axis values.
        y_col: Column name for y-axis values.
        title: Chart title displayed above the plot.
        color_col: Optional column to color points by.
        size_col: Optional column to determine point sizes.
        hover_cols: Additional columns to display in hover tooltip.
        height: Chart height in pixels.
        trendline: Whether to add OLS regression trendline.

    Returns:
        plotly.graph_objects.Figure ready for st.plotly_chart().
    """
    custom_data = []
    hover_template = f"<b>%{{x}}</b> vs <b>%{{y}}</b><extra></extra>"
    
    if hover_cols:
        for i, col in enumerate(hover_cols):
            if col in df.columns:
                custom_data.append(df[col])
                hover_template += f"<br>{col}: %{{customdata[{i}]}}"

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        size=size_col,
        title=title,
        template="plotly_white",
        height=height,
        trendline="ols" if trendline else None,
        custom_data=custom_data if custom_data else None,
        color_discrete_map={color_col: THEME.CHART_PRIMARY} 
            if color_col and color_col in df.columns else None,
    )

    if hover_template != "<b>%{x}</b> vs <b>%{y}</b><extra></extra>":
        fig.update_traces(hovertemplate=hover_template)

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
        margin=dict(l=60, r=40, t=80, b=60),
        xaxis_title=x_col.replace("_", " ").title(),
        yaxis_title=y_col.replace("_", " ").title(),
    )

    if trendline:
        for trace in fig.data:
            if "trendline" in str(trace.name).lower():
                trace.line.color = THEME.TEXT_WARNING
                trace.line.width = 2
                trace.line.dash = "dash"

    return fig
