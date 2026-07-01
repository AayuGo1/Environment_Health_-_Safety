"""
Heatmap Chart Module
=====================
Professional correlation matrix visualization for EHS analytics.
Returns valid plotly.graph_objects.Figure objects compatible with
st.plotly_chart(use_container_width=True).
"""

import plotly.graph_objects as go
from typing import Optional
import pandas as pd
import numpy as np

from config import THEME


def render_heatmap_chart(
    df: pd.DataFrame,
    title: str = "Correlation Matrix",
    annot: bool = True,
    colorscale: str = "RdBu_r",
    height: int = 600,
    zmin: float = -1.0,
    zmax: float = 1.0,
) -> go.Figure:
    """
    Creates a professional annotated heatmap for correlation analysis.

    Args:
        df: Square DataFrame with numeric correlation values.
        title: Chart title displayed above the plot.
        annot: Whether to display correlation coefficient values in cells.
        colorscale: Plotly colorscale name (e.g., 'RdBu_r', 'Viridis').
        height: Chart height in pixels.
        zmin: Minimum value for color scale normalization.
        zmax: Maximum value for color scale normalization.

    Returns:
        plotly.graph_objects.Figure ready for st.plotly_chart().
    """
    # Prepare annotation text
    if annot:
        z_text = np.round(df.values, 2).astype(str)
        z_text = np.where(pd.isna(df.values), "", z_text)
    else:
        z_text = None

    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns.tolist(),
        y=df.index.tolist(),
        zmin=zmin,
        zmax=zmax,
        colorscale=colorscale,
        text=z_text,
        texttemplate="%{text}",
        textfont=dict(size=10, color="white"),
        hoverongaps=False,
        hovertemplate=(
            "<b>%{y}</b> vs <b>%{x}</b><br>"
            "Correlation: %{z:.3f}<extra></extra>"
        ),
        colorbar=dict(
            title="Correlation",
            titleside="top",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["-1.0", "-0.5", "0.0", "0.5", "1.0"],
            len=0.8,
            thickness=15,
        ),
    ))

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=THEME.TEXT_DARK),
            x=0.5,
            xanchor="center",
        ),
        font=dict(family="Inter, sans-serif", size=11),
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=9),
            side="bottom",
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=9),
        ),
        margin=dict(l=150, r=50, t=80, b=150),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig
