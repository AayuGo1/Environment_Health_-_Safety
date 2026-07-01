"""
GitHub Data Loader Module
==========================
Manages downloading Excel workbooks from GitHub raw URLs with 
automatic retry, caching, and error handling. Ensures the dashboard
always displays the latest available data without manual intervention.
FIXED: Corrected cache import path and added robust error handling.
"""

import io
import logging
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import GITHUB
from utils.cache import get_cached_data, set_cached_data

logger = logging.getLogger(__name__)


class GitHubDataLoader:
    """Loads and caches Excel data from GitHub with resilience."""

    def __init__(self):
        self.url = GITHUB.raw_url
        self.timeout = 30  # seconds
        self.max_retries = 3

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True,
    )
    def _fetch_raw_content(self) -> bytes:
        """Fetches raw Excel content from GitHub with exponential backoff."""
        logger.info(f"Fetching data from: {self.url}")
        response = requests.get(self.url, timeout=self.timeout)
        response.raise_for_status()
        logger.info("Successfully downloaded Excel file")
        return response.content

    def load_workbook(self) -> Optional[Tuple[pd.ExcelFile, str]]:
        """
        Loads Excel workbook from GitHub or cache.
        
        Returns:
            Tuple of (ExcelFile object, last_updated_timestamp) or None on failure.
        """
        # Try cache first
        cached = get_cached_data()
        if cached is not None:
            logger.info("Serving data from cache")
            return cached

        try:
            content = self._fetch_raw_content()
            xls = pd.ExcelFile(io.BytesIO(content))
            timestamp = datetime.now().strftime("%d-%b-%y %H:%M")
            
            # Cache successful load
            set_cached_data(xls, timestamp)
            logger.info(f"Data loaded and cached. Timestamp: {timestamp}")
            return xls, timestamp
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"GitHub HTTP error ({e.response.status_code}): {e}")
            st.session_state.load_error = f"GitHub returned {e.response.status_code}. Check repo/file name."
            return None
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"GitHub connection failed: {e}")
            st.session_state.load_error = "Cannot connect to GitHub. Check internet/repo access."
            return None
            
        except Exception as e:
            logger.error(f"Failed to load/parse data: {e}", exc_info=True)
            st.session_state.load_error = f"Data loading error: {str(e)[:100]}"
            
            # Return cached data as fallback if available
            fallback = get_cached_data(force_stale=True)
            if fallback is not None:
                logger.warning("Using stale cached data due to load error")
                return fallback
            return None
