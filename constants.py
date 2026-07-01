# constants.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple
import re


class KPICategory(str, Enum):
    PRODUCTION = "Production"
    ENERGY = "Energy"
    WATER = "Water"
    WASTE = "Waste"
    HEALTH_SAFETY = "Health & Safety"
    ENVIRONMENT = "Environment"


@dataclass(frozen=True)
class ExcelParsingConstants:
    """Regex patterns and structural constants for Excel parsing."""
    
    MONTH_PATTERN: re.Pattern = re.compile(
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$',
        re.IGNORECASE
    )
    
    PERCENTAGE_PATTERN: re.Pattern = re.compile(r'^[\d.]+%$')
    
    NA_VALUES: Tuple[str, ...] = ("NA", "N/A", "na", "n/a", "-", "")
    
    HEADER_SEPARATOR: str = " | "
    
    # FIXED: Use default_factory for mutable dict in frozen dataclass
    SHEET_NAME_MAPPINGS: Dict[str, str] = field(default_factory=lambda: {
        "environment": "Environment",
        "h&s": "H&S",
        "health": "H&S",
        "safety": "H&S",
        "ehs": "Environment",
    })
    
    EXCLUDED_COLUMNS: Tuple[str, ...] = (
        "YTD", "Target", "BU", "Plant", "Department",
        "Category", "Subcategory", "KPI Name"
    )


@dataclass(frozen=True)
class KPIDisplayRules:
    LOWER_IS_BETTER_KEYWORDS: Tuple[str, ...] = (
        "fatality", "injury", "accident", "incident", "near miss",
        "intensity", "waste", "emission", "frequency rate",
        "days lost", "restricted work", "medical treatment"
    )
    
    HIGHER_IS_BETTER_KEYWORDS: Tuple[str, ...] = (
        "production", "volume", "recycled", "reused", "involvement",
        "closure", "participation", "trained", "observation"
    )
    
    DEFAULT_UNITS: Dict[str, str] = field(default_factory=lambda: {
        "kWh/Gross Weight": "kWh/MT",
        "m³/Gross Weight": "m³/MT",
        "kg/Gross Weight": "kg/MT",
        "Gross Weight (t Metric)": "MT",
        "[kWh]": "kWh",
        "[m³]": "m³",
        "[kg]": "kg",
        "[%]": "%",
    })
    
    SPARKLINE_MONTHS: int = 6
    PRECISION_INTENSITY: int = 2
    PRECISION_VOLUME: int = 0
    PRECISION_PERCENTAGE: int = 1
    PRECISION_COUNT: int = 0


EXCEL = ExcelParsingConstants()
KPI_RULES = KPIDisplayRules()
