"""
Enterprise EHS Dashboard Constants
====================================
Immutable business logic, KPI taxonomy, and Excel parsing patterns.
These constants drive dynamic discovery so NO sheet names, column names,
or KPI identifiers are ever hardcoded in UI or analytics code.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple
import re


class KPICategory(str, Enum):
    """Top-level KPI categories matching Excel sheet hierarchy."""
    PRODUCTION = "Production"
    ENERGY = "Energy"
    WATER = "Water"
    WASTE = "Waste"
    HEALTH_SAFETY = "Health & Safety"
    ENVIRONMENT = "Environment"


class IndicatorType(str, Enum):
    """H&S indicator classification."""
    LAGGING = "Lagging Indicators"
    LEADING = "Leading Indicators"
    NORMALIZED = "Normalized Metrics"
    KPI = "Health & Safety KPIs"


@dataclass(frozen=True)
class ExcelParsingConstants:
    """Regex patterns and structural constants for Excel parsing."""
    
    # Month column detection pattern (matches Apr-25, Mar-26, etc.)
    MONTH_PATTERN: re.Pattern = re.compile(
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$',
        re.IGNORECASE
    )
    
    # Percentage value pattern (matches "82%", "1.10%", etc.)
    PERCENTAGE_PATTERN: re.Pattern = re.compile(r'^[\d.]+%$')
    
    # NA/Null value representations in Excel
    NA_VALUES: Tuple[str, ...] = ("NA", "N/A", "na", "n/a", "-", "")
    
    # Multi-level header separator when flattening
    HEADER_SEPARATOR: str = " | "
    
    # Expected sheet names (case-insensitive matching)
    SHEET_NAME_MAPPINGS: Dict[str, str] = {
        "environment": "Environment",
        "h&s": "H&S",
        "health": "H&S",
        "safety": "H&S",
        "ehs": "Environment",
    }
    
    # Columns that should NEVER be treated as month columns
    EXCLUDED_COLUMNS: Tuple[str, ...] = (
        "YTD", "Target", "BU", "Plant", "Department",
        "Category", "Subcategory", "KPI Name"
    )


@dataclass(frozen=True)
class KPIDisplayRules:
    """Business rules for KPI rendering and status evaluation."""
    
    # KPIs where LOWER values are better (intensity, incidents, waste)
    LOWER_IS_BETTER_KEYWORDS: Tuple[str, ...] = (
        "fatality", "injury", "accident", "incident", "near miss",
        "intensity", "waste", "emission", "frequency rate",
        "days lost", "restricted work", "medical treatment"
    )
    
    # KPIs where HIGHER values are better (production, recycling %, involvement)
    HIGHER_IS_BETTER_KEYWORDS: Tuple[str, ...] = (
        "production", "volume", "recycled", "reused", "involvement",
        "closure", "participation", "trained", "observation"
    )
    
    # Default units by category
    DEFAULT_UNITS: Dict[str, str] = {
        "kWh/Gross Weight": "kWh/MT",
        "m³/Gross Weight": "m³/MT",
        "kg/Gross Weight": "kg/MT",
        "Gross Weight (t Metric)": "MT",
        "[kWh]": "kWh",
        "[m³]": "m³",
        "[kg]": "kg",
        "[%]": "%",
        "[L]": "L",
        "[SCM]": "SCM",
    }
    
    # Sparkline lookback period (number of months)
    SPARKLINE_MONTHS: int = 6
    
    # Decimal precision for different metric types
    PRECISION_INTENSITY: int = 2
    PRECISION_VOLUME: int = 0
    PRECISION_PERCENTAGE: int = 1
    PRECISION_COUNT: int = 0


# Singleton instances
EXCEL = ExcelParsingConstants()
KPI_RULES = KPIDisplayRules()
