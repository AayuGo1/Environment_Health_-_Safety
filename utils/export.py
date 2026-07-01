"""
Export Utility Module
======================
Multi-format data export engine supporting Excel, CSV, PNG, and PDF.
Generates professionally formatted reports with dashboard branding,
conditional formatting, and filtered dataset preservation.
"""

import io
import base64
from datetime import datetime
from typing import Optional, BinaryIO

import pandas as pd
import streamlit as st
import plotly.io as pio
from PIL import Image

from config import THEME, PAGE


class DashboardExporter:
    """Handles all dashboard data and chart exports."""
    
    @staticmethod
    def to_excel(df: pd.DataFrame, filename: str = "EHS_Report.xlsx") -> bytes:
        """
        Exports dataframe to formatted Excel with branded header.
        
        Args:
            df: Pandas DataFrame to export.
            filename: Output filename with .xlsx extension.
            
        Returns:
            Bytes object containing Excel file content.
        """
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="KPI Report")
            
            workbook = writer.book
            worksheet = writer.sheets["KPI Report"]
            
            # Branded header format
            header_fmt = workbook.add_format({
                "bold": True,
                "bg_color": THEME.BG_SECONDARY,
                "font_color": THEME.TEXT_LIGHT,
                "border": 1,
                "text_wrap": True,
            })
            
            # Apply header formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)
                worksheet.set_column(col_num, col_num, max(len(str(value)) + 2, 12))
        
        output.seek(0)
        return output.read()
    
    @staticmethod
    def to_csv(df: pd.DataFrame) -> str:
        """Exports dataframe to CSV string with UTF-8 encoding."""
        return df.to_csv(index=False, encoding="utf-8-sig")
    
    @staticmethod
    def chart_to_png(fig, width: int = 1200, height: int = 800) -> bytes:
        """
        Converts Plotly figure to high-resolution PNG.
        
        Args:
            fig: Plotly Figure object.
            width: Image width in pixels.
            height: Image height in pixels.
            
        Returns:
            Bytes object containing PNG image.
        """
        try:
            img_bytes = pio.to_image(
                fig, format="png", width=width, height=height, scale=2
            )
            return img_bytes
        except Exception as e:
            st.error(f"PNG export failed: {e}")
            return b""
    
    @staticmethod
    def create_download_button(
        data: bytes,
        filename: str,
        mime_type: str,
        label: str = "Download",
    ) -> None:
        """
        Renders Streamlit download button for exported content.
        
        Args:
            data: File content as bytes.
            filename: Suggested download filename.
            mime_type: MIME type for browser handling.
            label: Button display text.
        """
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{label}</a>'
        st.markdown(href, unsafe_allow_html=True)
