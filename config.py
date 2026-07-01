"""
Enterprise EHS Dashboard Configuration
========================================
Centralized configuration for theme, layout, and external integrations.
All visual constants and API endpoints are defined here to ensure 
consistency across all dashboard pages and components.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ThemeConfig:
    """Premium Enterprise Dark Navy Theme Palette."""
    
    # Backgrounds
    BG_PRIMARY: str = "#0B132B"       # Deep navy base
    BG_SECONDARY: str = "#1C2541"     # Slightly lighter for panels/sidebar
    BG_TERTIARY: str = "#3A506B"      # Accent background for active states
    
    # Card & Surface Colors
    CARD_BG: str = "#FFFFFF"          # Pure white for KPI cards/charts
    CARD_BORDER: str = "#E2E8F0"      # Subtle border for depth
    GLASS_BG: str = "rgba(28, 37, 65, 0.85)"  # Glassmorphism overlay
    
    # Typography
    TEXT_LIGHT: str = "#FFFFFF"       # Primary text on dark backgrounds
    TEXT_MUTED: str = "#A0AEC0"       # Secondary/label text
    TEXT_DARK: str = "#1A202C"        # Text on white cards
    TEXT_SUCCESS: str = "#38A169"     # Green for positive metrics
    TEXT_WARNING: str = "#DD6B20"     # Orange for warnings
    TEXT_DANGER: str = "#E53E3E"      # Red for critical issues
    
    # Chart Palette (Colorblind-safe & professional)
    CHART_PRIMARY: str = "#3182CE"    # Blue - Energy/Water trends
    CHART_SECONDARY: str = "#319795"  # Teal - Waste/Recycling
    CHART_ACCENT_1: str = "#805AD5"   # Purple - Safety observations
    CHART_ACCENT_2: str = "#D69E2E"   # Gold - Production volume
    CHART_GRID: str = "rgba(0,0,0,0.06)"  # Subtle grid lines
    
    # Status Indicators
    STATUS_ON_TRACK: str = "#38A169"
    STATUS_OFF_TRACK: str = "#E53E3E"
    STATUS_NO_TARGET: str = "#A0AEC0"


@dataclass(frozen=True)
class GitHubConfig:
    """GitHub Raw File Integration Settings."""
    
    REPO_OWNER: str = "AayuGo1"
    REPO_NAME: str = "Environment_Health_-_Safety"
    BRANCH: str = "main"
    EXCEL_FILENAME: str = "Monthly KPI Summary Sheet_April_GNSC.xlsx"
    
    @property
    def raw_url(self) -> str:
        """Constructs the direct raw content URL."""
        return (
            f"https://raw.githubusercontent.com/"
            f"{self.REPO_OWNER}/{self.REPO_NAME}/"
            f"{self.BRANCH}/{self.EXCEL_FILENAME}"
        )
    
    @property
    def cache_ttl(self) -> int:
        """Cache duration in seconds (1 hour)."""
        return 3600


@dataclass(frozen=True)
class PageConfig:
    """Streamlit Page Layout & Metadata."""
    
    TITLE: str = "EHS Dashboard | GNSC Plant"
    ICON: str = "🛡️"
    LAYOUT: str = "wide"
    SIDEBAR_STATE: str = "expanded"
    
    # Header Dimensions
    HEADER_HEIGHT_PX: int = 80
    LOGO_WIDTH_PX: int = 180


# Singleton instances for import convenience
THEME = ThemeConfig()
GITHUB = GitHubConfig()
PAGE = PageConfig()
