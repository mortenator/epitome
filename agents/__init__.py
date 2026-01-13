"""
Epitome Production Management Agents
Extraction and generation tools for production workbooks.
"""

from .prompts import EPITOME_EXTRACTION_SYSTEM_PROMPT
from .production_workbook_generator import EpitomeWorkbookGenerator, run_tool
from .enrichment import (
    enrich_production_data,
    get_location_coordinates,
    get_weather_data,
    get_company_logo,
    get_client_research
)

__all__ = [
    'EPITOME_EXTRACTION_SYSTEM_PROMPT',
    'EpitomeWorkbookGenerator',
    'run_tool',
    'enrich_production_data',
    'get_location_coordinates',
    'get_weather_data',
    'get_company_logo',
    'get_client_research'
]
