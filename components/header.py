"""
Header Component Module
========================
Enterprise-grade top navigation bar with glassmorphism styling,
dynamic timestamp updates, and responsive layout management.
Integrates seamlessly with Streamlit's native header while maintaining
custom branding and professional spacing.
"""

import streamlit as st
from config import THEME, PAGE


def render_header(last_updated: str = "Loading...") -> None:
    """
    Renders the main dashboard header with logo, title, and metadata.
    
    Args:
        last_updated: Timestamp string for data freshness indicator.
                      Defaults to 'Loading...' during initial render.
    """
    st.markdown(f"""
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 1.2rem 2rem;
            background: linear-gradient(135deg, {THEME.BG_SECONDARY} 0%, {THEME.BG_TERTIARY} 100%);
            border-radius: 0 0 20px 20px;
            margin-bottom: 2.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border-bottom: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
        ">
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <div style="
                    width: 48px; height: 48px;
                    background: {THEME.CHART_PRIMARY};
                    border-radius: 12px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 1.6rem;
                    box-shadow: 0 4px 12px rgba(49,130,206,0.4);
                ">🛡️</div>
                <div>
                    <div style="
                        color: {THEME.TEXT_LIGHT};
                        font-size: 1.75rem;
                        font-weight: 700;
                        letter-spacing: -0.02em;
                        margin-bottom: 0.2rem;
                    ">EHS DASHBOARD</div>
                    <div style="
                        color: {THEME.TEXT_MUTED};
                        font-size: 0.85rem;
                        font-weight: 500;
                        text-transform: uppercase;
                        letter-spacing: 0.08em;
                    ">Health, Safety & Environment | GNSC Plant</div>
                </div>
            </div>
            
            <div style="text-align: right;">
                <div style="
                    color: {THEME.TEXT_LIGHT};
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    margin-bottom: 0.3rem;
                    opacity: 0.8;
                ">Data As On</div>
                <div id="header-timestamp" style="
                    color: {THEME.TEXT_MUTED};
                    font-size: 1.1rem;
                    font-weight: 600;
                    font-variant-numeric: tabular-nums;
                ">{last_updated}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def update_timestamp_js(new_timestamp: str) -> None:
    """
    Updates the header timestamp without full page rerender.
    Uses JavaScript DOM manipulation for smooth UX.
    
    Args:
        new_timestamp: Formatted timestamp string to display.
    """
    st.components.v1.html(f"""
        <script>
            const el = document.getElementById('header-timestamp');
            if (el) el.innerText = '{new_timestamp}';
        </script>
    """, height=0)
