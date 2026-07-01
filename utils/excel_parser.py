"""
Excel Parser Module
====================
Dynamically parses H&S and Environment sheets with 3-level headers.
Discovers all KPIs, months, targets, and categories automatically.
Zero hardcoding - adapts to structural changes in monthly reports.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import pandas as pd

from constants import EXCEL, KPICategory, IndicatorType


@dataclass
class ParsedSheet:
    """Normalized representation of a parsed Excel sheet."""
    name: str
    category: KPICategory
    df_wide: pd.DataFrame          # Original wide format for card rendering
    df_long: pd.DataFrame          # Long format for charting/trends
    month_columns: List[str]       # Detected month columns
    kpi_metadata: Dict[str, Dict]  # KPI → {unit, target, lower_is_better}
    ytd_column: Optional[str]
    target_column: Optional[str]


class ExcelParser:
    """Parses Excel workbooks into normalized dashboard-ready data."""

    def __init__(self, xls: pd.ExcelFile):
        self.xls = xls
        self.sheet_map = self._build_sheet_mapping()

    def _build_sheet_mapping(self) -> Dict[str, str]:
        """Maps known sheet aliases to actual sheet names (case-insensitive)."""
        mapping = {}
        actual_sheets = {s.lower(): s for s in self.xls.sheet_names}
        for alias, canonical in EXCEL.SHEET_NAME_MAPPINGS.items():
            if alias in actual_sheets:
                mapping[canonical] = actual_sheets[alias]
        return mapping

    def parse_all(self) -> Dict[str, ParsedSheet]:
        """Parses all recognized sheets into normalized structures."""
        results = {}
        for category, sheet_name in self.sheet_map.items():
            parsed = self._parse_single_sheet(sheet_name, category)
            if parsed is not None:
                results[category] = parsed
        return results

    def _parse_single_sheet(
        self, sheet_name: str, category: KPICategory
    ) -> Optional[ParsedSheet]:
        """Parses a single sheet with 3-level header detection."""
        try:
            # Read with 3-row header
            df = pd.read_excel(self.xls, sheet_name=sheet_name, header=[0, 1, 2])
            
            # Flatten multi-index columns
            flat_cols = []
            for col in df.columns:
                parts = [
                    str(c).strip() 
                    for c in col 
                    if str(c).strip() not in ('nan', 'None', '')
                ]
                flat_cols.append(EXCEL.HEADER_SEPARATOR.join(parts) if parts else "Unnamed")
            df.columns = flat_cols
            
            # Detect month columns dynamically
            month_cols = [
                c for c in df.columns 
                if EXCEL.MONTH_PATTERN.search(c.split(EXCEL.HEADER_SEPARATOR)[-1].strip())
                and c not in EXCEL.EXCLUDED_COLUMNS
            ]
            
            # Detect YTD and Target columns
            ytd_col = next((c for c in df.columns if '|YTD' in c.upper()), None)
            target_col = next((c for c in df.columns if '|TARGET' in c.upper()), None)
            
            # Build KPI metadata
            kpi_meta = self._extract_kpi_metadata(df, month_cols, ytd_col, target_col)
            
            # Create long-format dataframe for charting
            id_vars = [c for c in df.columns if c not in month_cols]
            df_long = df.melt(id_vars=id_vars, value_vars=month_cols, 
                            var_name="Month", value_name="Value")
            
            return ParsedSheet(
                name=sheet_name,
                category=category,
                df_wide=df,
                df_long=df_long,
                month_columns=month_cols,
                kpi_metadata=kpi_meta,
                ytd_column=ytd_col,
                target_column=target_col,
            )
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to parse sheet '{sheet_name}': {e}")
            return None

    def _extract_kpi_metadata(
        self, df: pd.DataFrame, month_cols: List[str],
        ytd_col: Optional[str], target_col: Optional[str]
    ) -> Dict[str, Dict]:
        """Extracts unit, target, and directionality for each KPI."""
        from constants import KPI_RULES
        
        metadata = {}
        non_month_cols = [c for c in df.columns if c not in month_cols]
        
        for col in non_month_cols:
            parts = col.split(EXCEL.HEADER_SEPARATOR)
            kpi_name = parts[-1].strip() if len(parts) > 0 else col
            
            # Extract unit from bracket notation
            unit = ""
            for part in parts:
                if '[' in part and ']' in part:
                    unit = part.strip()
                    break
            
            # Determine if lower is better
            lower_better = any(
                kw in kpi_name.lower() 
                for kw in KPI_RULES.LOWER_IS_BETTER_KEYWORDS
            )
            
            # Get target value (first row assumed to be current period)
            target_val = None
            if target_col and target_col in df.columns:
                try:
                    target_val = float(df.iloc[0][target_col])
                except (ValueError, TypeError, IndexError):
                    pass
            
            metadata[kpi_name] = {
                "full_column": col,
                "unit": unit,
                "target": target_val,
                "lower_is_better": lower_better,
                "category": parts[0].strip() if len(parts) > 0 else "Unknown",
            }
        
        return metadata
