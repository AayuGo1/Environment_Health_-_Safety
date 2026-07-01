"""
Excel Parser Module
====================
Dynamically parses H&S and Environment sheets with 3-level headers.
Discovers all KPIs, months, targets, and categories automatically.
FIXED: Corrected data access pattern to treat KPIs as ROWS 
and months as COLUMNS, matching actual Excel workbook structure.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np

from constants import EXCEL, KPICategory

logger = logging.getLogger(__name__)


@dataclass
class ParsedSheet:
    """Normalized representation of a parsed Excel sheet."""
    name: str
    category: KPICategory
    df_wide: pd.DataFrame          # Wide format: Rows=KPIs, Cols=Months
    df_long: pd.DataFrame          # Long format for charting/trends
    month_columns: List[str]       # Detected month columns
    kpi_metadata: Dict[str, Dict]  # KPI Name → {full_column, unit, target, lower_is_better, row_idx}
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
            else:
                logger.warning(f"Failed to parse sheet '{sheet_name}', skipping.")
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
            
            # Build KPI metadata with ROW INDEX mapping
            kpi_meta = self._extract_kpi_metadata(df, month_cols, ytd_col, target_col)
            
            # Create long-format dataframe for charting
            # Melt only month columns; keep KPI identifier columns as id_vars
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
            logger.error(f"Failed to parse sheet '{sheet_name}': {e}", exc_info=True)
            return None

    def _extract_kpi_metadata(
        self, df: pd.DataFrame, month_cols: List[str],
        ytd_col: Optional[str], target_col: Optional[str]
    ) -> Dict[str, Dict]:
        """
        Extracts unit, target, directionality, and ROW INDEX for each KPI.
        FIXED: Now maps KPI names to their row index in df_wide for correct data access.
        """
        from constants import KPI_RULES
        
        metadata = {}
        non_month_cols = [c for c in df.columns if c not in month_cols]
        
        # Determine which column contains the KPI name/identifier
        # Usually it's the first non-month column or a specific named column
        kpi_id_col = next((c for c in non_month_cols if 'KPI' in c.upper() or 'NAME' in c.upper()), non_month_cols[0] if non_month_cols else None)
        
        for idx in range(len(df)):
            # Get the KPI identifier from this row
            kpi_identifier = str(df.iloc[idx][kpi_id_col]).strip() if kpi_id_col else f"Row_{idx}"
            
            # Find the most descriptive column name for this row's KPI
            # We'll use the first non-month, non-id column that has data as the "primary" column
            primary_data_col = None
            for col in non_month_cols:
                if col != kpi_id_col and not pd.isna(df.iloc[idx][col]):
                    val = str(df.iloc[idx][col]).strip()
                    if val and val not in EXCEL.NA_VALUES:
                        primary_data_col = col
                        break
            
            if primary_data_col is None:
                continue
                
            parts = primary_data_col.split(EXCEL.HEADER_SEPARATOR)
            kpi_name = parts[-1].strip() if len(parts) > 0 else primary_data_col
            
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
            
            # Get target value from the target column for THIS ROW
            target_val = None
            if target_col and target_col in df.columns:
                raw_target = df.iloc[idx][target_col]
                try:
                    if isinstance(raw_target, str) and '%' in raw_target:
                        target_val = float(raw_target.replace('%', ''))
                    else:
                        target_val = float(raw_target)
                except (ValueError, TypeError):
                    pass
            
            metadata[kpi_name] = {
                "full_column": primary_data_col,
                "unit": unit,
                "target": target_val,
                "lower_is_better": lower_better,
                "category": parts[0].strip() if len(parts) > 0 else "Unknown",
                "row_idx": idx,  # CRITICAL FIX: Store row index for data access
            }
        
        return metadata
