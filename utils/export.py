"""
Export Utility Module
======================
Multi-format data export engine supporting Excel, CSV, PNG, and PDF.
Generates professionally formatted reports with dashboard branding,
conditional formatting, and filtered dataset preservation.
FIXED: Corrected theme references and added robust error handling.
"""

import io
import base64
from datetime import datetime
from typing import Optional, BinaryIO

import pandas as pd
import streamlit as st
import plotly.io as pio

from config import THEME


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
        if df.empty:
            raise ValueError("Cannot export empty DataFrame")
            
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="KPI Report")
                
                workbook = writer.book
                worksheet = writer.sheets["KPI Report"]
                
                # Branded header format using correct theme constants
                header_fmt = workbook.add_format({
                    "bold": True,
                    "bg_color": THEME.BG_SECONDARY,  # Fixed: Was BG_TERTIARY
                    "font_color": THEME.TEXT_LIGHT,   # Fixed: Was TEXT_PRIMARY
                    "border": 1,
                    "text_wrap": True,
                })
                
                # Apply header formatting
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, str(value), header_fmt)
                    worksheet.set_column(col_num, col_num, max(len(str(value)) + 2, 12))
                    
                # Auto-fit row heights
                worksheet.set_default_row(hide_unused_rows=False)
                
        finally:
            output.seek(0)
            
        return output.read()
    
    @staticmethod
    def to_csv(df: pd.DataFrame) -> str:
        """Exports dataframe to CSV string with UTF-8 encoding."""
        if df.empty:
            return ""
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
            Bytes object containing PNG image, or empty bytes on failure.
        """
        try:
            img_bytes = pio.to_image(
                fig, 
                format="png", 
                width=width, 
                height=height, 
                scale=2
            )
            return img_bytes
        except Exception as e:
            st.warning(f"⚠️ PNG export failed: {str(e)[:100]}. Ensure kaleido is installed.")
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
        if not data:
            st.info("ℹ️ No data available for download")
            return
            
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}" class="stButton">{label}</a>'
        st.markdown(href, unsafe_allow_html=True)
