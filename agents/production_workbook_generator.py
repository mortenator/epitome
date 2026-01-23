"""
Epitome Production Workbook Generator
Generates multi-tab Excel workbooks for production management using xlsxwriter.
"""

import xlsxwriter
import json
import os
import re
from datetime import datetime
from typing import Callable, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without it

from google import genai
from .prompts import EPITOME_EXTRACTION_SYSTEM_PROMPT
from .enrichment import enrich_production_data


class EpitomeWorkbookGenerator:
    """
    Generates a production workbook based on the Epitome template.
    Includes: Crew List, Daily Call Sheets, Schedule, Locations, and PO Log.
    """

    def __init__(self, data: dict, output_filename: str = "production_workbook.xlsx"):
        self.data = data
        self.output_filename = output_filename
        self.workbook = xlsxwriter.Workbook(self.output_filename)
        self.formats = {}

        # Define standard Layout/Styles
        self._init_formats()

    def _init_formats(self):
        """Initialize Excel formats for consistent branding."""
        # Main Headers
        self.formats['header_dark'] = self.workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': '#111827',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12
        })
        self.formats['header_light'] = self.workbook.add_format({
            'bold': True, 'font_color': 'black', 'bg_color': '#F3F4F6',
            'border': 1, 'align': 'left', 'valign': 'vcenter'
        })

        # Data Cells
        self.formats['cell_normal'] = self.workbook.add_format({'border': 1, 'valign': 'vcenter'})
        self.formats['cell_center'] = self.workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        self.formats['cell_bold'] = self.workbook.add_format({'border': 1, 'bold': True, 'valign': 'vcenter'})

        # Section Dividers (Department Headers)
        self.formats['dept_header'] = self.workbook.add_format({
            'bold': True, 'bg_color': '#D1D5DB', 'border': 1, 'align': 'left'
        })

        # Title
        self.formats['title_large'] = self.workbook.add_format({
            'bold': True, 'font_size': 18, 'align': 'left'
        })

        # ============================================
        # CALL SHEET DASHBOARD FORMATS
        # ============================================

        # Large title banner (36pt for "CALL SHEET" header)
        self.formats['cs_title_banner'] = self.workbook.add_format({
            'bold': True, 'font_size': 36, 'align': 'center', 'valign': 'vcenter'
        })

        # Job info header (14pt bold)
        self.formats['cs_job_info'] = self.workbook.add_format({
            'bold': True, 'font_size': 14, 'valign': 'vcenter'
        })

        # Date/day display (12pt)
        self.formats['cs_date'] = self.workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'right', 'valign': 'vcenter'
        })

        # Call time large emphasis (18pt)
        self.formats['cs_call_time_large'] = self.workbook.add_format({
            'bold': True, 'font_size': 18, 'align': 'left', 'valign': 'vcenter'
        })

        # Call time medium (14pt)
        self.formats['cs_call_time_medium'] = self.workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'left', 'valign': 'vcenter'
        })

        # Section label (10pt bold, top-aligned)
        self.formats['cs_label'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'top'
        })

        # Section value (10-11pt, top-aligned)
        self.formats['cs_value'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'top'
        })

        # Section value bold
        self.formats['cs_value_bold'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'top', 'bold': True
        })

        # Crew grid header (black bg, white text, 10pt)
        self.formats['cs_grid_header'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'bg_color': '#000000',
            'font_color': 'white', 'align': 'left', 'valign': 'vcenter'
        })

        # Crew grid header centered
        self.formats['cs_grid_header_center'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'bg_color': '#000000',
            'font_color': 'white', 'align': 'center', 'valign': 'vcenter'
        })

        # Department header inline (black bg, spans partial row)
        self.formats['cs_dept_header'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'bg_color': '#000000',
            'font_color': 'white', 'valign': 'vcenter'
        })

        # Crew data cell (no border, clean)
        self.formats['cs_crew_cell'] = self.workbook.add_format({
            'font_size': 11, 'valign': 'vcenter'
        })

        # Crew data cell centered (for call times)
        self.formats['cs_crew_cell_center'] = self.workbook.add_format({
            'font_size': 10, 'align': 'center', 'valign': 'vcenter'
        })

        # Footer section header
        self.formats['cs_footer_header'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'bg_color': '#000000',
            'font_color': 'white', 'valign': 'vcenter'
        })

        # ============================================
        # BORDER-AWARE FORMATS (for grid fidelity)
        # ============================================

        # Data cell with white fill and thin borders (internal cells)
        self.formats['cs_data_cell'] = self.workbook.add_format({
            'font_size': 11,
            'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'border': 1,
            'border_color': '#000000'
        })

        # Data cell centered with borders
        self.formats['cs_data_cell_center'] = self.workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'border': 1,
            'border_color': '#000000'
        })

        # Data cell left edge (thick left border - column A)
        self.formats['cs_data_cell_left'] = self.workbook.add_format({
            'font_size': 11,
            'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2,
            'right': 1,
            'top': 1,
            'bottom': 1,
            'border_color': '#000000'
        })

        # Data cell right edge (thick right border - column F separator)
        self.formats['cs_data_cell_right'] = self.workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1,
            'right': 2,
            'top': 1,
            'bottom': 1,
            'border_color': '#000000'
        })

        # Data cell right edge last column (thick right - column L)
        self.formats['cs_data_cell_right_last'] = self.workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1,
            'right': 2,
            'top': 1,
            'bottom': 1,
            'border_color': '#000000'
        })

        # Grid header left edge (thick left + thin others)
        self.formats['cs_grid_header_left'] = self.workbook.add_format({
            'bold': True,
            'font_size': 10,
            'bg_color': '#000000',
            'font_color': 'white',
            'left': 2,
            'right': 1,
            'top': 2,  # THICK top for grid perimeter
            'bottom': 1,
            'border_color': '#000000'
        })

        # Grid header internal (thick top for grid perimeter)
        self.formats['cs_grid_header_internal'] = self.workbook.add_format({
            'bold': True,
            'font_size': 10,
            'bg_color': '#000000',
            'font_color': 'white',
            'left': 1,
            'right': 1,
            'top': 2,  # THICK top for grid perimeter
            'bottom': 1,
            'border_color': '#000000'
        })

        # Grid header internal centered (thick top for grid perimeter)
        self.formats['cs_grid_header_internal_center'] = self.workbook.add_format({
            'bold': True,
            'font_size': 10,
            'bg_color': '#000000',
            'font_color': 'white',
            'align': 'center',
            'left': 1,
            'right': 1,
            'top': 2,  # THICK top for grid perimeter
            'bottom': 1,
            'border_color': '#000000'
        })

        # Grid header right edge (thick right - F column, thick top)
        self.formats['cs_grid_header_right'] = self.workbook.add_format({
            'bold': True,
            'font_size': 10,
            'bg_color': '#000000',
            'font_color': 'white',
            'align': 'center',
            'left': 1,
            'right': 2,
            'top': 2,  # THICK top for grid perimeter
            'bottom': 1,
            'border_color': '#000000'
        })

        # Grid header right edge last (thick right - L column, thick top)
        self.formats['cs_grid_header_right_last'] = self.workbook.add_format({
            'bold': True,
            'font_size': 10,
            'bg_color': '#000000',
            'font_color': 'white',
            'align': 'center',
            'left': 1,
            'right': 2,
            'top': 2,  # THICK top for grid perimeter
            'bottom': 1,
            'border_color': '#000000'
        })

        # Department header left section (A-F) - black with borders
        self.formats['cs_dept_left'] = self.workbook.add_format({
            'bold': True,
            'font_size': 10,
            'bg_color': '#000000',
            'font_color': 'white',
            'left': 2,
            'right': 1,
            'top': 1,
            'bottom': 1,
            'border_color': '#000000'
        })

        self.formats['cs_dept_internal'] = self.workbook.add_format({
            'bg_color': '#000000',
            'border': 1,
            'border_color': '#000000'
        })

        self.formats['cs_dept_right'] = self.workbook.add_format({
            'bg_color': '#000000',
            'left': 1,
            'right': 2,
            'top': 1,
            'bottom': 1,
            'border_color': '#000000'
        })

        # Footer section with borders
        self.formats['cs_footer_header_bordered'] = self.workbook.add_format({
            'bold': True,
            'font_size': 10,
            'bg_color': '#000000',
            'font_color': 'white',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000'
        })

        self.formats['cs_footer_cell'] = self.workbook.add_format({
            'font_size': 10,
            'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'border': 1,
            'border_color': '#000000'
        })

        # ============================================
        # HEADER ZONE FORMATS (Rows 1-14)
        # ============================================

        # Title banner row 1 - black fill, white text, thick top border
        self.formats['cs_banner_topleft'] = self.workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 2, 'top': 2, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_banner_top'] = self.workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'top': 2, 'bottom': 1, 'left': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_banner_topright'] = self.workbook.add_format({
            'bold': True, 'font_size': 12, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter', 'align': 'right',
            'right': 2, 'top': 2, 'bottom': 1, 'left': 1,
            'border_color': '#000000'
        })

        # Title banner main (36pt centered)
        self.formats['cs_banner_main'] = self.workbook.add_format({
            'bold': True, 'font_size': 36, 'font_color': 'white',
            'bg_color': '#000000', 'align': 'center', 'valign': 'vcenter',
            'top': 2, 'bottom': 1, 'left': 1, 'right': 1,
            'border_color': '#000000'
        })

        # Title banner row 2 - black fill, no top border emphasis
        self.formats['cs_banner_left'] = self.workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 2, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_banner_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 12, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter', 'align': 'right',
            'right': 2, 'top': 1, 'bottom': 1, 'left': 1,
            'border_color': '#000000'
        })

        # Black fill for empty cells in banner rows
        self.formats['cs_banner_fill'] = self.workbook.add_format({
            'bg_color': '#000000',
            'top': 1, 'bottom': 1, 'left': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_banner_fill_top'] = self.workbook.add_format({
            'bg_color': '#000000',
            'top': 2, 'bottom': 1, 'left': 1, 'right': 1,
            'border_color': '#000000'
        })

        # Section labels (bold, with borders) - different positions
        self.formats['cs_label_left'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'left': 2, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_label'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_label_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        # Header data cells (white fill, bordered)
        self.formats['cs_hdr_data_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_hdr_data'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_hdr_data_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        self.formats['cs_hdr_data_bold'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        # Large call times (18pt)
        self.formats['cs_call_large'] = self.workbook.add_format({
            'bold': True, 'font_size': 18, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_call_large_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 18, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        # Medium call times (14pt)
        self.formats['cs_call_medium'] = self.workbook.add_format({
            'bold': True, 'font_size': 14, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_call_medium_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 14, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        # Bottom edge of header zone (thick bottom)
        self.formats['cs_hdr_bottom_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 1, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_hdr_bottom'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_hdr_bottom_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 2, 'right': 2,
            'border_color': '#000000'
        })

        # ============================================
        # "OUTSIDE-ONLY" SECTION FORMATS (Rows 9-14)
        # These formats create perimeter-only borders
        # ============================================

        # Row 9 labels - top border, no bottom (connects to section below)
        self.formats['cs_label_section_top'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 0, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_label_section_top_left'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 1, 'bottom': 0, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_label_section_top_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 0, 'right': 2,
            'border_color': '#000000'
        })

        # Section middle rows (10-13) - only left/right borders, no top/bottom
        self.formats['cs_section_mid'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 0, 'bottom': 0, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_section_mid_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 0, 'bottom': 0, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_section_mid_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 0, 'bottom': 0, 'right': 2,
            'border_color': '#000000'
        })

        self.formats['cs_section_mid_bold'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 0, 'bottom': 0, 'right': 1,
            'border_color': '#000000'
        })

        # Section bottom row (14) - only bottom/left/right, no top
        self.formats['cs_section_bottom'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 0, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_section_bottom_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 0, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_section_bottom_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 0, 'bottom': 2, 'right': 2,
            'border_color': '#000000'
        })

        # ============================================
        # "BOX" FORMATS FOR ROWS 3-8 (OUTSIDE-ONLY BORDERS)
        # Each section has only perimeter borders, no internal lines
        # ============================================

        # Top-left corner (thick left for A column)
        self.formats['cs_box_topleft_thick'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 2, 'top': 1, 'bottom': 0, 'right': 0,
            'border_color': '#000000'
        })

        # Top-left corner (thin left for internal sections)
        self.formats['cs_box_topleft'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 0, 'right': 0,
            'border_color': '#000000'
        })

        # Top edge (no left/right)
        self.formats['cs_box_top'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 1, 'bottom': 0, 'right': 0,
            'border_color': '#000000'
        })

        # Top-right corner (thin right)
        self.formats['cs_box_topright'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 1, 'bottom': 0, 'right': 1,
            'border_color': '#000000'
        })

        # Top-right corner (thick right for L column)
        self.formats['cs_box_topright_thick'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 1, 'bottom': 0, 'right': 2,
            'border_color': '#000000'
        })

        # Left edge only (thick)
        self.formats['cs_box_left_thick'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 2, 'top': 0, 'bottom': 0, 'right': 0,
            'border_color': '#000000'
        })

        # Left edge only (thin)
        self.formats['cs_box_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 1, 'top': 0, 'bottom': 0, 'right': 0,
            'border_color': '#000000'
        })

        # Center (NO borders)
        self.formats['cs_box_center'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'border': 0
        })

        # Right edge only (thin)
        self.formats['cs_box_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 0, 'right': 1,
            'border_color': '#000000'
        })

        # Right edge only (thick)
        self.formats['cs_box_right_thick'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 0, 'right': 2,
            'border_color': '#000000'
        })

        # Bottom-left (thick left)
        self.formats['cs_box_bottomleft_thick'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 2, 'top': 0, 'bottom': 1, 'right': 0,
            'border_color': '#000000'
        })

        # Bottom-left (thin)
        self.formats['cs_box_bottomleft'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 1, 'top': 0, 'bottom': 1, 'right': 0,
            'border_color': '#000000'
        })

        # Bottom edge (no left/right)
        self.formats['cs_box_bottom'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 1, 'right': 0,
            'border_color': '#000000'
        })

        # Bottom-right (thin)
        self.formats['cs_box_bottomright'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        # Bottom-right (thick)
        self.formats['cs_box_bottomright_thick'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        # ============================================
        # CREW GRID THICK PERIMETER FORMATS
        # ============================================

        # Top row of grid (thick top border)
        self.formats['cs_data_top'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 2, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_data_top_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 2, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_data_top_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 2, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        self.formats['cs_data_top_center'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'align': 'center',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 2, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        # Bottom row of grid (thick bottom border)
        self.formats['cs_data_bottom'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_data_bottom_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 1, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_data_bottom_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 2, 'right': 2,
            'border_color': '#000000'
        })

        self.formats['cs_data_bottom_center'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter', 'align': 'center',
            'bg_color': '#FFFFFF',
            'left': 1, 'top': 1, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        # Department headers for top/bottom positions
        self.formats['cs_dept_top_left'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 2, 'top': 2, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_dept_top_internal'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 1, 'top': 2, 'bottom': 1, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_dept_top_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 1, 'top': 2, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        self.formats['cs_dept_bottom_left'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 2, 'top': 1, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_dept_bottom_internal'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 1, 'top': 1, 'bottom': 2, 'right': 1,
            'border_color': '#000000'
        })

        self.formats['cs_dept_bottom_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'font_color': 'white',
            'bg_color': '#000000', 'valign': 'vcenter',
            'left': 1, 'top': 1, 'bottom': 2, 'right': 2,
            'border_color': '#000000'
        })

        # ============================================
        # FOOTER SECTION FORMATS (Rows 44-50)
        # "PRODUCTION REPORT NOTES" header and thick bottom border
        # ============================================

        # "PRODUCTION REPORT NOTES" header (spans full width)
        self.formats['cs_notes_header_left'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#D9D9D9',
            'left': 2, 'top': 2, 'bottom': 1, 'right': 0,
            'border_color': '#000000'
        })

        self.formats['cs_notes_header_center'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#D9D9D9',
            'left': 0, 'top': 2, 'bottom': 1, 'right': 0,
            'border_color': '#000000'
        })

        self.formats['cs_notes_header_right'] = self.workbook.add_format({
            'bold': True, 'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#D9D9D9',
            'left': 0, 'top': 2, 'bottom': 1, 'right': 2,
            'border_color': '#000000'
        })

        # Notes area rows (45-49) - just side borders
        self.formats['cs_notes_left'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 0, 'bottom': 0, 'right': 0,
            'border_color': '#000000'
        })

        self.formats['cs_notes_center'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 0, 'right': 0,
            'border_color': '#000000'
        })

        self.formats['cs_notes_right'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 0, 'right': 2,
            'border_color': '#000000'
        })

        # Row 50 - Footer row with thick BOTTOM border
        self.formats['cs_footer_bottomleft'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 2, 'top': 0, 'bottom': 2, 'right': 0,
            'border_color': '#000000'
        })

        self.formats['cs_footer_bottom'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 2, 'right': 0,
            'border_color': '#000000'
        })

        self.formats['cs_footer_bottomright'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 2, 'right': 2,
            'border_color': '#000000'
        })

        # Additional footer formats with divider (column F thick right)
        self.formats['cs_footer_bottom_divider'] = self.workbook.add_format({
            'font_size': 10, 'valign': 'vcenter',
            'bg_color': '#FFFFFF',
            'left': 0, 'top': 0, 'bottom': 2, 'right': 2,
            'border_color': '#000000'
        })

    def generate(self):
        """Orchestrates the generation of all sheets matching sample workbook structure."""
        # Core sheets
        self._write_crew_list()
        self._write_schedule()

        # Dynamic Call Sheets (One per scheduled day)
        days = self.data.get('schedule_days', [{'day_number': 1, 'date': 'TBD'}])
        for day in days:
            self._write_call_sheet(day)

        # Additional production sheets
        self._write_po_log()
        self._write_credits_list()
        self._write_locations()
        self._write_key_crew()
        self._write_overages()
        self._write_transpo()
        self._write_pick_up_list()
        self._write_travel()
        self._write_travel_memo()
        self._write_wrap_notes()

        self.workbook.close()
        return self.output_filename

    # ==========================================
    # SHEET 1: CREW LIST
    # ==========================================
    def _write_crew_list(self):
        ws = self.workbook.add_worksheet('Crew List')
        ws.set_column('A:A', 25) # Dept/Role
        ws.set_column('B:B', 25) # Name
        ws.set_column('C:C', 15) # Phone
        ws.set_column('D:D', 25) # Email
        ws.set_column('E:E', 15) # Rate

        # Header Info
        prod_info = self.data.get('production_info', {})
        job_name = prod_info.get('job_name', 'TBD')
        job_number = prod_info.get('job_number', '')
        client = prod_info.get('client', 'TBD')
        
        ws.write('A1', f"JOB: {job_name}", self.formats['title_large'])
        if job_number and job_number != 'TBD':
            ws.write('A2', f"JOB #: {job_number}")
            ws.write('A3', f"CLIENT: {client}")
        else:
            ws.write('A2', f"CLIENT: {client}")

        # Table Headers
        headers = ['Role', 'Name', 'Phone', 'Email', 'Rate', 'Notes']
        for col, h in enumerate(headers):
            ws.write(3, col, h, self.formats['header_dark'])

        # Write Crew Data
        row = 4
        current_dept = None

        # Sort crew by department for cleaner grouping if possible, otherwise use input order
        crew = self.data.get('crew_list', [])

        # Default buckets if empty
        if not crew:
            departments = ['Production', 'Camera', 'G&E', 'Art', 'Sound', 'H/MU', 'Wardrobe', 'PA']
            for dept in departments:
                ws.merge_range(row, 0, row, 5, dept.upper(), self.formats['dept_header'])
                row += 1
                for _ in range(3): # Add a few blank lines per dept
                    ws.write_blank(row, 0, None, self.formats['cell_normal'])
                    row += 1
            return

        # If we have data
        for person in crew:
            dept = person.get('department', 'General')
            if dept != current_dept:
                ws.merge_range(row, 0, row, 5, dept.upper(), self.formats['dept_header'])
                row += 1
                current_dept = dept

            ws.write(row, 0, person.get('role', ''), self.formats['cell_bold'])
            ws.write(row, 1, person.get('name', ''), self.formats['cell_normal'])
            ws.write(row, 2, person.get('phone', ''), self.formats['cell_normal'])
            ws.write(row, 3, person.get('email', ''), self.formats['cell_normal'])
            ws.write(row, 4, person.get('rate', ''), self.formats['cell_normal'])
            ws.write(row, 5, person.get('notes', ''), self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 2: CALL SHEET (Dynamic per Day) - DASHBOARD LAYOUT
    # ==========================================
    def _write_call_sheet(self, day_info):
        day_num = day_info.get('day_number', 1)
        total_days = len(self.data.get('schedule_days', [1]))
        ws_name = f"Call Sheet - Day {day_num}"
        ws = self.workbook.add_worksheet(ws_name)

        # ============================================
        # GRID SYSTEM: 12-column dashboard layout
        # ============================================
        ws.set_column('A:A', 27.0)   # Title/Role
        ws.set_column('B:B', 22.9)   # Name
        ws.set_column('C:C', 12.5)   # Phone
        ws.set_column('D:D', 26.6)   # Email
        ws.set_column('E:E', 6.4)    # Call (narrow)
        ws.set_column('F:F', 9.9)    # Loc (narrow)
        ws.set_column('G:G', 34.0)   # Talent Title (wide)
        ws.set_column('H:H', 21.4)   # Talent Name
        ws.set_column('I:I', 12.5)   # Talent Phone
        ws.set_column('J:J', 23.9)   # Talent Email
        ws.set_column('K:K', 9.4)    # Talent Call
        ws.set_column('L:L', 10.5)   # Talent Loc

        # Hide gridlines for clean dashboard look
        ws.hide_gridlines(2)

        # Set row heights for header zone
        ws.set_row(0, 21.75)  # Row 1
        ws.set_row(1, 21.75)  # Row 2

        # ============================================
        # DATA EXTRACTION
        # ============================================
        prod_info = self.data.get('production_info', {})
        logistics = self.data.get('logistics', {})
        locs = logistics.get('locations', [])
        main_loc = locs[0] if locs else {}
        parking_loc = locs[1] if len(locs) > 1 else main_loc

        # Weather from day_info (enriched) or fallback
        day_weather = day_info.get('weather', {})
        weather = day_weather if day_weather else logistics.get('weather', {})
        hosp = logistics.get('hospital', {})

        # ============================================
        # HEADER ZONE: Rows 1-14 (Styled dashboard)
        # ============================================
        self._write_call_sheet_header_zone(ws, day_info, prod_info, logistics)

        # ============================================
        # CREW GRID: Row 16+ (Dual-column layout)
        # ============================================
        self._write_call_sheet_crew_grid(ws, day_info, start_row=15)

    def _write_call_sheet_header_zone(self, ws, day_info: dict, prod_info: dict, logistics: dict):
        """Write header zone (rows 1-14) with full styling matching sample template."""
        day_num = day_info.get('day_number', 1)
        total_days = len(self.data.get('schedule_days', [1]))

        # Extract data
        locs = logistics.get('locations', [])
        main_loc = locs[0] if locs else {}
        parking_loc = locs[1] if len(locs) > 1 else main_loc
        day_weather = day_info.get('weather', {})
        weather = day_weather if day_weather else logistics.get('weather', {})
        hosp = logistics.get('hospital', {})

        job_name = prod_info.get('job_name', 'TBD')
        job_number = prod_info.get('job_number', '')
        date_str = day_info.get('date', 'TBD')
        crew_call = day_info.get('crew_call', 'TBD')
        prod_call = day_info.get('production_call', crew_call)
        breakfast_time = day_info.get('breakfast_time', 'TBD')
        talent_call = day_info.get('talent_call', 'SEE BELOW')

        # ============================================
        # ROWS 1-2: Title Banner (BLACK FILL)
        # ============================================
        # Row 1: A1:B1 job name | C1:I1 (part of C1:I2 merge) | J1:L1 date
        ws.merge_range('A1:B1', f"Job Name: {job_name}", self.formats['cs_banner_topleft'])
        ws.merge_range('C1:I2', f"CALL SHEET - SHOOT DAY {day_num}", self.formats['cs_banner_main'])
        ws.merge_range('J1:L1', date_str, self.formats['cs_banner_topright'])

        # Row 2: A2:B2 job number | (C2:I2 already merged) | J2:L2 day counter
        ws.merge_range('A2:B2', f"Job #: {job_number}", self.formats['cs_banner_left'])
        ws.merge_range('J2:L2', f"SHOOT DAY {day_num} OF {total_days}", self.formats['cs_banner_right'])

        # ============================================
        # ROWS 3-8: Section boxes with OUTSIDE-ONLY borders
        # Each section (A:B, C:E, F:G, H:I, J:L) has only perimeter borders
        # ============================================

        # === SECTION A3:B8 (Production Company) - thick left edge ===
        # Row 3 (top of box)
        ws.write('A3', "PRODUCTION COMPANY:", self.formats['cs_box_topleft_thick'])
        ws.write('B3', "", self.formats['cs_box_topright'])

        # Rows 4-7 (middle of box - only left/right borders)
        ws.write('A4', "", self.formats['cs_box_left_thick'])
        ws.write('B4', "", self.formats['cs_box_right'])
        ws.write('A5', prod_info.get('production_company', 'Epitome'), self.formats['cs_box_left_thick'])
        ws.write('B5', "", self.formats['cs_box_right'])
        ws.write('A6', prod_info.get('address', ''), self.formats['cs_box_left_thick'])
        ws.write('B6', "", self.formats['cs_box_right'])
        ws.write('A7', "", self.formats['cs_box_left_thick'])
        ws.write('B7', "", self.formats['cs_box_right'])

        # Row 8 (bottom of box)
        ws.write('A8', "", self.formats['cs_box_bottomleft_thick'])
        ws.write('B8', "", self.formats['cs_box_bottomright'])

        # === SECTION C3:E8 (Client) - thin edges ===
        # Row 3 (top of box)
        ws.write('C3', "CLIENT:", self.formats['cs_box_topleft'])
        ws.write('D3', "", self.formats['cs_box_top'])
        ws.write('E3', "", self.formats['cs_box_topright'])

        # Rows 4-7 (middle of box - only left/right borders)
        ws.write('C4', "", self.formats['cs_box_left'])
        ws.write('D4', "", self.formats['cs_box_center'])
        ws.write('E4', "", self.formats['cs_box_right'])
        ws.write('C5', prod_info.get('client', 'TBD'), self.formats['cs_box_left'])
        ws.write('D5', "", self.formats['cs_box_center'])
        ws.write('E5', "", self.formats['cs_box_right'])
        ws.write('C6', prod_info.get('client_address', ''), self.formats['cs_box_left'])
        ws.write('D6', "", self.formats['cs_box_center'])
        ws.write('E6', "", self.formats['cs_box_right'])
        ws.write('C7', prod_info.get('client_address_2', ''), self.formats['cs_box_left'])
        ws.write('D7', "", self.formats['cs_box_center'])
        ws.write('E7', "", self.formats['cs_box_right'])

        # Row 8 (bottom of box)
        ws.write('C8', "", self.formats['cs_box_bottomleft'])
        ws.write('D8', "", self.formats['cs_box_bottom'])
        ws.write('E8', "", self.formats['cs_box_bottomright'])

        # === SECTION F3:G8 (Filming Location) - thin edges ===
        # Row 3 (top of box)
        ws.merge_range('F3:G3', "FILMING LOCATION 1:", self.formats['cs_box_topleft'])

        # Rows 4-7 (middle of box)
        ws.write('F4', "", self.formats['cs_box_left'])
        ws.write('G4', "", self.formats['cs_box_right'])
        ws.merge_range('F5:G5', main_loc.get('name', 'TBD'), self.formats['cs_box_left'])
        ws.merge_range('F6:G6', main_loc.get('address', ''), self.formats['cs_box_left'])
        ws.merge_range('F7:G7', main_loc.get('address_line_2', ''), self.formats['cs_box_left'])

        # Row 8 (bottom of box)
        ws.merge_range('F8:G8', "", self.formats['cs_box_bottomleft'])

        # === SECTION H3:I8 (Hospitals) - thin edges ===
        # Row 3 (top of box)
        ws.merge_range('H3:I3', "HOSPITALS:", self.formats['cs_box_topleft'])

        # Rows 4-7 (middle of box)
        ws.write('H4', "", self.formats['cs_box_left'])
        ws.write('I4', "", self.formats['cs_box_right'])
        ws.merge_range('H5:I5', hosp.get('name', 'TBD'), self.formats['cs_box_left'])
        ws.merge_range('H6:I6', hosp.get('address', ''), self.formats['cs_box_left'])
        ws.merge_range('H7:I7', hosp.get('address_line_2', ''), self.formats['cs_box_left'])

        # Row 8 (bottom of box)
        ws.merge_range('H8:I8', "", self.formats['cs_box_bottomleft'])

        # === SECTION J3:L8 (Call Times / Weather) - thick right edge ===
        # Row 3 (top of box)
        ws.write('J3', "GENERAL CREW CALL:", self.formats['cs_box_topleft'])
        ws.write('K3', "PRODUCTION CALL:", self.formats['cs_box_top'])
        ws.write('L3', "", self.formats['cs_box_topright_thick'])

        # Rows 4-5 (merged call times)
        ws.merge_range('J4:J5', crew_call, self.formats['cs_call_large'])
        ws.merge_range('K4:L5', prod_call, self.formats['cs_call_medium_right'])

        # Row 6 (middle labels)
        ws.write('J6', "COURTESY BFAST RTS:", self.formats['cs_box_left'])
        ws.write('K6', "TALENT CALL:", self.formats['cs_box_center'])
        ws.write('L6', "", self.formats['cs_box_right_thick'])

        # Rows 7-8 (merged call times)
        ws.merge_range('J7:J8', breakfast_time, self.formats['cs_call_medium'])
        ws.merge_range('K7:L8', talent_call, self.formats['cs_call_medium_right'])

        # ============================================
        # ROW 9: Section Headers (top of "outside-only" bordered sections)
        # Uses formats with TOP border only (no bottom), connecting to data below
        # ============================================
        ws.merge_range('A9:B9', "PRODUCTION CELLS:", self.formats['cs_label_section_top_left'])
        ws.merge_range('C9:E9', "LABEL/AGENCY:", self.formats['cs_label_section_top'])
        ws.merge_range('F9:G9', "CREW PARKING", self.formats['cs_label_section_top'])
        ws.merge_range('H9:I9', "TRUCK PARKING", self.formats['cs_label_section_top'])
        ws.merge_range('J9:L9', f"WEATHER: {weather.get('conditions', '')}", self.formats['cs_label_section_top_right'])

        # ============================================
        # ROWS 10-13: Contact Info + Weather Details (MIDDLE of sections)
        # Uses formats with ONLY left/right borders (no top, no bottom)
        # ============================================
        # Weather details
        temp = weather.get('temperature', {})
        if isinstance(temp, dict):
            high_temp = temp.get('high', '°F')
            low_temp = temp.get('low', '°F')
        else:
            high_temp = weather.get('high', '°F')
            low_temp = weather.get('low', '°F')

        # Row 10 (first data row - only left/right borders)
        ws.merge_range('A10:B10', "", self.formats['cs_section_mid_left'])
        ws.merge_range('C10:E10', "", self.formats['cs_section_mid'])
        ws.merge_range('F10:G10', "", self.formats['cs_section_mid'])
        ws.merge_range('H10:I10', main_loc.get('name', ''), self.formats['cs_section_mid'])
        ws.merge_range('J10:L10', f"High: {high_temp}", self.formats['cs_section_mid_right'])

        # Row 11 (middle data row - only left/right borders)
        producer = self._get_crew_by_role('Producer')
        ws.merge_range('A11:B11', f"Producer: {producer.get('name', '')} - {producer.get('phone', '')}", self.formats['cs_section_mid_left'])
        ws.merge_range('C11:E11', "", self.formats['cs_section_mid'])
        ws.merge_range('F11:G11', parking_loc.get('parking', 'TBD'), self.formats['cs_section_mid_bold'])
        ws.merge_range('H11:I11', main_loc.get('truck_parking', ''), self.formats['cs_section_mid'])
        ws.merge_range('J11:L11', f"Low: {low_temp}", self.formats['cs_section_mid_right'])

        # Row 12 (middle data row - only left/right borders)
        prod_mgr = self._get_crew_by_role('Production Manager')
        ws.merge_range('A12:B12', f"Prod. Manager: {prod_mgr.get('name', '')} - {prod_mgr.get('phone', '')}", self.formats['cs_section_mid_left'])
        ws.merge_range('C12:E12', "", self.formats['cs_section_mid'])
        ws.merge_range('F12:G12', "", self.formats['cs_section_mid'])
        ws.merge_range('H12:I12', "", self.formats['cs_section_mid'])
        ws.merge_range('J12:L12', f"Sunrise: {weather.get('sunrise', 'TBD')}", self.formats['cs_section_mid_right'])

        # Row 13 (middle data row - only left/right borders)
        ws.merge_range('A13:B13', "", self.formats['cs_section_mid_left'])
        ws.merge_range('C13:E13', "", self.formats['cs_section_mid'])
        ws.merge_range('F13:G13', "", self.formats['cs_section_mid'])
        ws.merge_range('H13:I13', "", self.formats['cs_section_mid'])
        ws.merge_range('J13:L13', f"Sunset: {weather.get('sunset', 'TBD')}", self.formats['cs_section_mid_right'])

        # ============================================
        # ROW 14: Bottom edge of sections (thick bottom border, no top)
        # ============================================
        ws.merge_range('A14:B14', "", self.formats['cs_section_bottom_left'])
        ws.merge_range('C14:E14', "", self.formats['cs_section_bottom'])
        ws.merge_range('F14:G14', "", self.formats['cs_section_bottom'])
        ws.merge_range('H14:I14', "", self.formats['cs_section_bottom'])
        ws.merge_range('J14:L14', f"Precip: {weather.get('precipitation', 'TBD')}", self.formats['cs_section_bottom_right'])

    def _get_crew_by_role(self, role: str) -> dict:
        """Helper to find a crew member by role."""
        crew = self.data.get('crew_list', [])
        for person in crew:
            if person.get('role', '').lower() == role.lower():
                return person
        return {}

    def _write_call_sheet_crew_grid(self, ws, day_info, start_row: int):
        """Write dynamic crew grid - compact when data provided, full template when empty.

        Behavior:
        - WITH crew data: Compact list, NO empty rows, footer moves up dynamically
        - WITHOUT crew data: Full template matching sample file structure
        """
        HEADER_ROW = 14        # Row 15 (0-indexed)
        DATA_START_ROW = 15    # Row 16 (0-indexed)

        row = HEADER_ROW

        # --- CREW DATA PREPARATION ---
        crew = self.data.get('crew_list', [])
        crew_call = day_info.get('crew_call', 'TBD')
        talent_call = day_info.get('talent_call', 'TBD')

        # Separate crew into left (production/camera/grip) and right (talent/vanity)
        right_departments = ['Talent', 'Vanity', 'H/MU', 'Wardrobe', 'Hair', 'Makeup', 'Management', 'MGMT', 'Production Support']

        left_crew = []
        right_crew = []

        for person in crew:
            dept = person.get('department', 'Production')
            if any(d.lower() in dept.lower() for d in right_departments):
                right_crew.append(person)
            else:
                left_crew.append(person)

        # If no crew data, use default template (matches sample file)
        if not crew:
            left_crew = self._get_default_left_crew()
            right_crew = self._get_default_right_crew()

        # --- PRE-CALCULATE grid end row for thick bottom border ---
        # Count rows needed for each side (dept headers + crew members)
        left_total_rows = self._count_crew_rows(left_crew)
        right_total_rows = self._count_crew_rows(right_crew)
        grid_end_row = DATA_START_ROW + max(left_total_rows, right_total_rows) - 1

        # --- HEADER ROW (Row 15 - thick TOP border) ---
        # Left table headers (A-F) with thick top
        ws.write(row, 0, "TITLE", self.formats['cs_grid_header_left'])       # A: thick left + top
        ws.write(row, 1, "NAME", self.formats['cs_grid_header_internal'])    # B: thick top
        ws.write(row, 2, "PHONE", self.formats['cs_grid_header_internal'])   # C: thick top
        ws.write(row, 3, "EMAIL", self.formats['cs_grid_header_internal'])   # D: thick top
        ws.write(row, 4, "CALL", self.formats['cs_grid_header_internal_center'])  # E: thick top
        ws.write(row, 5, "LOC", self.formats['cs_grid_header_right'])        # F: thick right + top

        # Right table headers (G-L) - Talent with thick top
        ws.write(row, 6, "TALENT", self.formats['cs_grid_header_left'])      # G: thick left + top
        ws.write(row, 7, "NAME", self.formats['cs_grid_header_internal'])    # H: thick top
        ws.write(row, 8, "PHONE", self.formats['cs_grid_header_internal'])   # I: thick top
        ws.write(row, 9, "EMAIL", self.formats['cs_grid_header_internal'])   # J: thick top
        ws.write(row, 10, "CALL", self.formats['cs_grid_header_internal_center'])  # K: thick top
        ws.write(row, 11, "LOC", self.formats['cs_grid_header_right_last'])  # L: thick right + top

        # --- DATA ROWS (Dynamic - no empty row padding) ---
        left_row = DATA_START_ROW
        right_row = DATA_START_ROW

        # Track current department for section headers
        left_dept = None
        right_dept = None

        # Process left side (crew) - compact, no empty rows
        for person in left_crew:
            dept = person.get('department', 'Production')
            is_last = (left_row == grid_end_row)

            if dept != left_dept:
                # Write department header spanning A-F with borders
                self._write_dept_header_left(ws, left_row, dept.upper(), is_last=is_last, grid_end_row=grid_end_row)
                left_dept = dept
                left_row += 1
                is_last = (left_row == grid_end_row)

            # Write crew data row with borders
            self._write_crew_row_left(ws, left_row, person, crew_call, is_last=is_last, grid_end_row=grid_end_row)
            left_row += 1

        # Process right side (talent/vanity) - compact, no empty rows
        for person in right_crew:
            dept = person.get('department', 'Talent')
            is_last = (right_row == grid_end_row)

            if dept != right_dept:
                # Write department header spanning G-L with borders
                self._write_dept_header_right(ws, right_row, dept.upper(), is_last=is_last, grid_end_row=grid_end_row)
                right_dept = dept
                right_row += 1
                is_last = (right_row == grid_end_row)

            # Write talent data row with borders
            call_time = talent_call if 'talent' in dept.lower() else crew_call
            self._write_crew_row_right(ws, right_row, person, call_time, is_last=is_last, grid_end_row=grid_end_row)
            right_row += 1

        # Fill shorter side with empty rows up to grid_end_row (to maintain thick bottom border alignment)
        while left_row <= grid_end_row:
            is_last = (left_row == grid_end_row)
            self._write_empty_row_left(ws, left_row, is_last=is_last)
            left_row += 1

        while right_row <= grid_end_row:
            is_last = (right_row == grid_end_row)
            self._write_empty_row_right(ws, right_row, is_last=is_last)
            right_row += 1

        # ============================================
        # FOOTER SECTIONS (Dynamic position after crew grid)
        # ============================================
        footer_start_row = grid_end_row + 1
        self._write_call_sheet_footer(ws, footer_start_row)

    def _count_crew_rows(self, crew_list: list) -> int:
        """Count total rows needed for a crew list (including department headers)."""
        if not crew_list:
            return 0
        total = 0
        seen_depts = set()
        for person in crew_list:
            dept = person.get('department', 'Unknown')
            if dept not in seen_depts:
                seen_depts.add(dept)
                total += 1  # Department header row
            total += 1  # Crew member row
        return total

    def _write_dept_header_left(self, ws, row: int, dept_name: str, is_last: bool = False, grid_end_row: int = 0):
        """Write department header for left section (A-F) with borders.

        Args:
            is_last: If True, this is the last row - use thick bottom border
            grid_end_row: The row number where the grid ends (for thick bottom)
        """
        if is_last or row == grid_end_row:
            # Last row - thick bottom border
            ws.write(row, 0, dept_name, self.formats['cs_dept_bottom_left'])
            ws.write(row, 1, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 2, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 3, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 4, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 5, '', self.formats['cs_dept_bottom_right'])
        else:
            # Normal row
            ws.write(row, 0, dept_name, self.formats['cs_dept_left'])
            ws.write(row, 1, '', self.formats['cs_dept_internal'])
            ws.write(row, 2, '', self.formats['cs_dept_internal'])
            ws.write(row, 3, '', self.formats['cs_dept_internal'])
            ws.write(row, 4, '', self.formats['cs_dept_internal'])
            ws.write(row, 5, '', self.formats['cs_dept_right'])

    def _write_dept_header_right(self, ws, row: int, dept_name: str, is_last: bool = False, grid_end_row: int = 0):
        """Write department header for right section (G-L) with borders.

        Args:
            is_last: If True, this is the last row - use thick bottom border
            grid_end_row: The row number where the grid ends (for thick bottom)
        """
        if is_last or row == grid_end_row:
            # Last row - thick bottom border
            ws.write(row, 6, dept_name, self.formats['cs_dept_bottom_left'])
            ws.write(row, 7, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 8, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 9, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 10, '', self.formats['cs_dept_bottom_internal'])
            ws.write(row, 11, '', self.formats['cs_dept_bottom_right'])
        else:
            # Normal row
            ws.write(row, 6, dept_name, self.formats['cs_dept_left'])
            ws.write(row, 7, '', self.formats['cs_dept_internal'])
            ws.write(row, 8, '', self.formats['cs_dept_internal'])
            ws.write(row, 9, '', self.formats['cs_dept_internal'])
            ws.write(row, 10, '', self.formats['cs_dept_internal'])
            ws.write(row, 11, '', self.formats['cs_dept_right'])

    def _write_crew_row_left(self, ws, row: int, person: dict, default_call: str, is_last: bool = False, grid_end_row: int = 0):
        """Write a single crew member row for left section (A-F) with borders.

        Args:
            is_last: If True, this is the last row - use thick bottom border
            grid_end_row: The row number where the grid ends (for thick bottom)
        """
        if is_last or row == grid_end_row:
            # Last row - thick bottom border
            ws.write(row, 0, person.get('role', ''), self.formats['cs_data_bottom_left'])
            ws.write(row, 1, person.get('name', ''), self.formats['cs_data_bottom'])
            ws.write(row, 2, person.get('phone', ''), self.formats['cs_data_bottom'])
            ws.write(row, 3, person.get('email', ''), self.formats['cs_data_bottom'])
            ws.write(row, 4, person.get('call_time', default_call), self.formats['cs_data_bottom_center'])
            ws.write(row, 5, person.get('location', ''), self.formats['cs_data_bottom_right'])
        else:
            # Normal row
            ws.write(row, 0, person.get('role', ''), self.formats['cs_data_cell_left'])
            ws.write(row, 1, person.get('name', ''), self.formats['cs_data_cell'])
            ws.write(row, 2, person.get('phone', ''), self.formats['cs_data_cell'])
            ws.write(row, 3, person.get('email', ''), self.formats['cs_data_cell'])
            ws.write(row, 4, person.get('call_time', default_call), self.formats['cs_data_cell_center'])
            ws.write(row, 5, person.get('location', ''), self.formats['cs_data_cell_right'])

    def _write_crew_row_right(self, ws, row: int, person: dict, default_call: str, is_last: bool = False, grid_end_row: int = 0):
        """Write a single crew member row for right section (G-L) with borders.

        Args:
            is_last: If True, this is the last row - use thick bottom border
            grid_end_row: The row number where the grid ends (for thick bottom)
        """
        if is_last or row == grid_end_row:
            # Last row - thick bottom border
            ws.write(row, 6, person.get('role', ''), self.formats['cs_data_bottom_left'])
            ws.write(row, 7, person.get('name', ''), self.formats['cs_data_bottom'])
            ws.write(row, 8, person.get('phone', ''), self.formats['cs_data_bottom'])
            ws.write(row, 9, person.get('email', ''), self.formats['cs_data_bottom'])
            ws.write(row, 10, person.get('call_time', default_call), self.formats['cs_data_bottom_center'])
            ws.write(row, 11, person.get('location', ''), self.formats['cs_data_bottom_right'])
        else:
            # Normal row
            ws.write(row, 6, person.get('role', ''), self.formats['cs_data_cell_left'])
            ws.write(row, 7, person.get('name', ''), self.formats['cs_data_cell'])
            ws.write(row, 8, person.get('phone', ''), self.formats['cs_data_cell'])
            ws.write(row, 9, person.get('email', ''), self.formats['cs_data_cell'])
            ws.write(row, 10, person.get('call_time', default_call), self.formats['cs_data_cell_center'])
            ws.write(row, 11, person.get('location', ''), self.formats['cs_data_cell_right_last'])

    def _write_empty_row_left(self, ws, row: int, is_last: bool = False):
        """Write an empty row for left section (A-F) with proper borders.

        Args:
            is_last: If True, use thick bottom border for row 43
        """
        if is_last:
            # Row 43 - thick bottom border
            ws.write(row, 0, '', self.formats['cs_data_bottom_left'])
            ws.write(row, 1, '', self.formats['cs_data_bottom'])
            ws.write(row, 2, '', self.formats['cs_data_bottom'])
            ws.write(row, 3, '', self.formats['cs_data_bottom'])
            ws.write(row, 4, '', self.formats['cs_data_bottom'])
            ws.write(row, 5, '', self.formats['cs_data_bottom_right'])
        else:
            # Normal empty row
            ws.write(row, 0, '', self.formats['cs_data_cell_left'])
            ws.write(row, 1, '', self.formats['cs_data_cell'])
            ws.write(row, 2, '', self.formats['cs_data_cell'])
            ws.write(row, 3, '', self.formats['cs_data_cell'])
            ws.write(row, 4, '', self.formats['cs_data_cell'])
            ws.write(row, 5, '', self.formats['cs_data_cell_right'])

    def _write_empty_row_right(self, ws, row: int, is_last: bool = False):
        """Write an empty row for right section (G-L) with proper borders.

        Args:
            is_last: If True, use thick bottom border for row 43
        """
        if is_last:
            # Row 43 - thick bottom border
            ws.write(row, 6, '', self.formats['cs_data_bottom_left'])
            ws.write(row, 7, '', self.formats['cs_data_bottom'])
            ws.write(row, 8, '', self.formats['cs_data_bottom'])
            ws.write(row, 9, '', self.formats['cs_data_bottom'])
            ws.write(row, 10, '', self.formats['cs_data_bottom'])
            ws.write(row, 11, '', self.formats['cs_data_bottom_right'])
        else:
            # Normal empty row
            ws.write(row, 6, '', self.formats['cs_data_cell_left'])
            ws.write(row, 7, '', self.formats['cs_data_cell'])
            ws.write(row, 8, '', self.formats['cs_data_cell'])
            ws.write(row, 9, '', self.formats['cs_data_cell'])
            ws.write(row, 10, '', self.formats['cs_data_cell'])
            ws.write(row, 11, '', self.formats['cs_data_cell_right_last'])

    def _get_default_left_crew(self) -> list:
        """Default crew skeleton for left side of call sheet.

        Matches sample file structure with full department sections:
        - PRODUCTION (12 roles)
        - CAMERA (3 roles)
        - STILLS (5 roles)
        - GRIP (4 roles)
        """
        return [
            # PRODUCTION (12 roles)
            {'department': 'Production', 'role': 'Director', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Executive Producer', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Producer', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Production Manager', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': '1st AD', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': '2nd AD', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Production Assistant - Truck', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Production Assistant - Set', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Production Assistant - Set', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Production Assistant - Set', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Production Assistant - Set', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production', 'role': 'Production Assistant - Driver', 'name': '', 'phone': '', 'email': ''},
            # CAMERA (3 roles)
            {'department': 'Camera', 'role': 'Director of Photography', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Camera', 'role': '1st AC', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Camera', 'role': '2nd AC / Cam PA', 'name': '', 'phone': '', 'email': ''},
            # STILLS (5 roles)
            {'department': 'Stills', 'role': 'Photographer', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Stills', 'role': '1st Assist', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Stills', 'role': '2nd Assist', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Stills', 'role': '3rd Assist', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Stills', 'role': 'Digi Tech', 'name': '', 'phone': '', 'email': ''},
            # GRIP (4 roles)
            {'department': 'Grip', 'role': 'Gaffer', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Grip', 'role': 'BBG', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Grip', 'role': 'Grip', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Grip', 'role': 'Grip', 'name': '', 'phone': '', 'email': ''},
        ]

    def _get_default_right_crew(self) -> list:
        """Default crew skeleton for right side (talent/vanity).

        Matches sample file structure with full department sections:
        - TALENT (5 roles)
        - MGMT (5 roles)
        - VANITY (6 roles)
        - PRODUCTION SUPPORT (3 placeholder rows)
        """
        return [
            # TALENT (5 roles)
            {'department': 'Talent', 'role': 'Talent 1', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Talent', 'role': 'Talent 2', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Talent', 'role': 'Talent 3', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Talent', 'role': 'Talent 4', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Talent', 'role': 'Talent 5', 'name': '', 'phone': '', 'email': ''},
            # MGMT (5 roles)
            {'department': 'MGMT', 'role': 'MGMT', 'name': '', 'phone': '', 'email': ''},
            {'department': 'MGMT', 'role': 'MGMT', 'name': '', 'phone': '', 'email': ''},
            {'department': 'MGMT', 'role': 'MGMT', 'name': '', 'phone': '', 'email': ''},
            {'department': 'MGMT', 'role': 'MGMT', 'name': '', 'phone': '', 'email': ''},
            {'department': 'MGMT', 'role': 'MGMT', 'name': '', 'phone': '', 'email': ''},
            # VANITY (6 roles)
            {'department': 'Vanity', 'role': 'Stylist', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Vanity', 'role': 'Stylist Assistant', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Vanity', 'role': 'Hair Stylist', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Vanity', 'role': 'Hair Assist', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Vanity', 'role': 'Makeup Artist', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Vanity', 'role': 'MU Assist', 'name': '', 'phone': '', 'email': ''},
            # PRODUCTION SUPPORT (3 placeholder rows)
            {'department': 'Production Support', 'role': '', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production Support', 'role': '', 'name': '', 'phone': '', 'email': ''},
            {'department': 'Production Support', 'role': '', 'name': '', 'phone': '', 'email': ''},
        ]

    def _write_call_sheet_footer(self, ws, start_row: int):
        """Write footer section matching sample structure.

        Fixed structure:
        - Row 44 (start_row): "PRODUCTION REPORT NOTES" header with thick top border
        - Rows 45-49: Notes area with side borders only
        - Row 50: Empty row with thick BOTTOM border (completes thick perimeter)
        """
        # Constants for fixed footer structure
        NOTES_HEADER_ROW = start_row      # Row 44 (0-indexed: 43)
        NOTES_START_ROW = start_row + 1   # Row 45 (0-indexed: 44)
        NOTES_END_ROW = start_row + 5     # Row 49 (0-indexed: 48)
        FOOTER_ROW = start_row + 6        # Row 50 (0-indexed: 49) - thick bottom

        # === ROW 44: "PRODUCTION REPORT NOTES" header with thick top border ===
        # Left section: "PRODUCTION REPORT NOTES" spanning A-F
        ws.write(NOTES_HEADER_ROW, 0, "PRODUCTION REPORT NOTES", self.formats['cs_notes_header_left'])
        for col in range(1, 5):
            ws.write(NOTES_HEADER_ROW, col, "", self.formats['cs_notes_header_center'])
        ws.write(NOTES_HEADER_ROW, 5, "", self.formats['cs_notes_header_right'])  # F has thick right for divider

        # Right section: empty header spanning G-L
        ws.write(NOTES_HEADER_ROW, 6, "", self.formats['cs_notes_header_left'])
        for col in range(7, 11):
            ws.write(NOTES_HEADER_ROW, col, "", self.formats['cs_notes_header_center'])
        ws.write(NOTES_HEADER_ROW, 11, "", self.formats['cs_notes_header_right'])

        # === ROWS 45-49: Notes area with side borders only ===
        for row in range(NOTES_START_ROW, NOTES_END_ROW + 1):
            # Left section (A-F)
            ws.write(row, 0, "", self.formats['cs_notes_left'])  # A: thick left
            for col in range(1, 5):
                ws.write(row, col, "", self.formats['cs_notes_center'])  # B-E: no borders
            ws.write(row, 5, "", self.formats['cs_notes_right'])  # F: thick right (divider)

            # Right section (G-L)
            ws.write(row, 6, "", self.formats['cs_notes_left'])  # G: thick left
            for col in range(7, 11):
                ws.write(row, col, "", self.formats['cs_notes_center'])  # H-K: no borders
            ws.write(row, 11, "", self.formats['cs_notes_right'])  # L: thick right

        # === ROW 50: Footer row with thick BOTTOM border (completes perimeter) ===
        # Left section (A-F)
        ws.write(FOOTER_ROW, 0, "", self.formats['cs_footer_bottomleft'])  # A: thick left + bottom
        for col in range(1, 5):
            ws.write(FOOTER_ROW, col, "", self.formats['cs_footer_bottom'])  # B-E: thick bottom
        ws.write(FOOTER_ROW, 5, "", self.formats['cs_footer_bottom_divider'])  # F: thick bottom + right (divider)

        # Right section (G-L)
        ws.write(FOOTER_ROW, 6, "", self.formats['cs_footer_bottomleft'])  # G: thick left + bottom
        for col in range(7, 11):
            ws.write(FOOTER_ROW, col, "", self.formats['cs_footer_bottom'])  # H-K: thick bottom
        ws.write(FOOTER_ROW, 11, "", self.formats['cs_footer_bottomright'])  # L: thick right + bottom


    # ==========================================
    # SHEET 3: SCHEDULE
    # ==========================================
    def _write_schedule(self):
        ws = self.workbook.add_worksheet('Schedule')
        ws.set_column('A:A', 15)  # Time
        ws.set_column('B:B', 40)  # Activity
        ws.set_column('C:C', 30)  # Notes

        ws.write('A1', "SHOOT SCHEDULE", self.formats['title_large'])

        headers = ['TIME', 'ACTIVITY / SCENE', 'NOTES']
        for col, h in enumerate(headers):
            ws.write(3, col, h, self.formats['header_dark'])

        # Get schedule from data, or use default template
        schedule = self.data.get('schedule', [])

        if not schedule:
            # Default schedule template when none provided
            schedule = [
                {"time": "07:00 AM", "activity": "CREW CALL / BREAKFAST", "notes": "Catering Tent"},
                {"time": "08:00 AM", "activity": "Safety Meeting", "notes": "All Hands"},
                {"time": "08:15 AM", "activity": "Shoot Scene 1", "notes": "TBD"},
                {"time": "01:00 PM", "activity": "LUNCH", "notes": "30 Mins"},
                {"time": "01:30 PM", "activity": "Shoot Scene 2", "notes": "TBD"},
                {"time": "07:00 PM", "activity": "WRAP", "notes": "Estimated"}
            ]

        row = 4
        for item in schedule:
            ws.write(row, 0, item.get('time', ''), self.formats['cell_center'])
            ws.write(row, 1, item.get('activity', ''), self.formats['cell_normal'])
            ws.write(row, 2, item.get('notes', ''), self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 4: LOCATIONS
    # ==========================================
    def _write_locations(self):
        ws = self.workbook.add_worksheet('Locations')
        ws.set_column('A:A', 20)
        ws.set_column('B:B', 30)
        ws.set_column('C:C', 20)
        ws.set_column('D:D', 15)
        ws.set_column('E:E', 15)
        ws.set_column('F:F', 25)
        ws.set_column('G:G', 25)

        headers = ['Location Name', 'Address', 'GPS Coordinates', 'Contact', 'Phone', 'Parking Notes', 'Nearest Hospital']
        for col, h in enumerate(headers):
            ws.write(0, col, h, self.formats['header_dark'])

        locs = self.data.get('logistics', {}).get('locations', [])
        hosp = self.data.get('logistics', {}).get('hospital', {})
        hosp_info = f"{hosp.get('name', 'TBD')} - {hosp.get('address', '')}" if hosp else "TBD"

        row = 1
        for loc in locs:
            ws.write(row, 0, loc.get('name', ''), self.formats['cell_bold'])
            ws.write(row, 1, loc.get('formatted_address', loc.get('address', '')), self.formats['cell_normal'])

            # GPS Coordinates from enrichment
            coords = loc.get('coordinates', {})
            if coords:
                coord_str = f"{coords.get('lat', '')}, {coords.get('lng', '')}"
            else:
                coord_str = 'TBD'
            ws.write(row, 2, coord_str, self.formats['cell_normal'])

            ws.write(row, 3, loc.get('contact', ''), self.formats['cell_normal'])
            ws.write(row, 4, loc.get('phone', ''), self.formats['cell_normal'])
            ws.write(row, 5, loc.get('parking', ''), self.formats['cell_normal'])
            ws.write(row, 6, hosp_info, self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 5: PO LOG
    # ==========================================
    def _write_po_log(self):
        ws = self.workbook.add_worksheet('PO Log')
        ws.set_column('A:H', 15)

        title = f"PO LOG - {self.data.get('production_info', {}).get('job_name', '')}"
        ws.merge_range('A1:H1', title, self.formats['title_large'])

        headers = ['PO #', 'Vendor', 'Description', 'Amount', 'Date', 'Pay Status', 'Notes', 'Budget Code']
        for col, h in enumerate(headers):
            ws.write(3, col, h, self.formats['header_dark'])

        # Add blank rows for entry
        for r in range(4, 20):
            for c in range(8):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 6: CREDITS LIST
    # ==========================================
    def _write_credits_list(self):
        ws = self.workbook.add_worksheet('Credits List')
        ws.set_column('A:A', 25)
        ws.set_column('B:B', 25)
        ws.set_column('C:C', 20)

        ws.write('A1', "CREDITS LIST", self.formats['header_dark'])

        headers = ['Production', 'Name', 'Instagram (@)']
        for col, h in enumerate(headers):
            ws.write(1, col, h, self.formats['dept_header'])

        # Standard production roles for credits
        roles = [
            'Director', 'Executive Producer', 'Producer', 'Production Manager',
            'Production Coordinator', '1st AD', '2nd AD', 'Director of Photography',
            'Camera Operator', '1st AC', 'Gaffer', 'Key Grip', 'HMU', 'Wardrobe Stylist',
            'Production Designer', 'Art Director', 'Editor', 'Colorist', 'Sound Mixer'
        ]

        row = 2
        for role in roles:
            ws.write(row, 0, role, self.formats['cell_bold'])
            ws.write_blank(row, 1, None, self.formats['cell_normal'])
            ws.write_blank(row, 2, None, self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 7: KEY CREW
    # ==========================================
    def _write_key_crew(self):
        ws = self.workbook.add_worksheet('Key Crew')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 25)
        ws.set_column('C:C', 20)
        ws.set_column('D:D', 15)
        ws.set_column('E:E', 25)
        ws.set_column('F:I', 15)

        ws.merge_range('A1:I1', "Key Crew Options", self.formats['header_dark'])

        headers = ['#', 'Name', 'Website', 'Phone', 'Email', 'Rate/Fees', 'Holds', 'Agency', 'Agency Email']
        for col, h in enumerate(headers):
            ws.write(1, col, h, self.formats['dept_header'])

        # Key crew categories
        categories = [
            'Director of Photography', 'Gaffer', 'Key Grip', 'Production Designer',
            'HMU', 'Wardrobe Stylist', 'Editor', 'Colorist'
        ]

        row = 2
        for category in categories:
            ws.write(row, 0, category, self.formats['cell_bold'])
            ws.merge_range(row, 1, row, 8, '', self.formats['cell_normal'])
            row += 1
            # Add 3 option rows per category
            for i in range(1, 4):
                ws.write(row, 0, f'{i}.0', self.formats['cell_center'])
                for c in range(1, 9):
                    ws.write_blank(row, c, None, self.formats['cell_normal'])
                row += 1

    # ==========================================
    # SHEET 8: OVERAGES
    # ==========================================
    def _write_overages(self):
        ws = self.workbook.add_worksheet('Overages')
        ws.set_column('A:L', 15)

        ws.merge_range('A1:L1', "OVERAGES TRACKER", self.formats['header_dark'])

        headers = ['Department', 'Description', 'Budgeted', 'Actual', 'Overage', 'Notes']
        for col, h in enumerate(headers):
            ws.write(2, col, h, self.formats['dept_header'])

        # Add blank rows for entry
        for r in range(3, 20):
            for c in range(6):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 9: TRANSPO
    # ==========================================
    def _write_transpo(self):
        ws = self.workbook.add_worksheet('Transpo')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 20)
        ws.set_column('C:C', 20)
        ws.set_column('D:K', 12)

        ws.merge_range('A1:K1', "Transportation & Rental Grid", self.formats['header_dark'])

        # Day headers row
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        ws.write(1, 5, 'Day of Week', self.formats['dept_header'])
        for i, day in enumerate(days):
            ws.write(1, 6 + i, day, self.formats['dept_header'])

        ws.write(2, 5, 'Date', self.formats['cell_bold'])
        ws.write(3, 5, 'Prep/Shoot/Wrap', self.formats['cell_bold'])

        # Column headers
        headers = ['#', 'Vehicle Type', 'Vendor', 'Days Used', 'Price', 'Driver']
        for col, h in enumerate(headers):
            ws.write(4, col, h, self.formats['dept_header'])

        # Add blank rows for vehicles
        for r in range(5, 15):
            ws.write(r, 0, f'{r - 4}.0', self.formats['cell_center'])
            for c in range(1, 11):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 10: PICK UP LIST
    # ==========================================
    def _write_pick_up_list(self):
        ws = self.workbook.add_worksheet('Pick Up List')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 25)
        ws.set_column('C:C', 30)
        ws.set_column('D:G', 15)

        ws.merge_range('A1:G1', "Pick Up List", self.formats['header_dark'])

        headers = ['#', 'Name', 'Address', 'Phone', 'Date', 'Time', 'What']
        for col, h in enumerate(headers):
            ws.write(1, col, h, self.formats['dept_header'])

        ws.write(2, 0, 'Driver:', self.formats['cell_bold'])
        ws.merge_range(2, 1, 2, 6, '', self.formats['cell_normal'])

        # Add blank rows for pickups
        for r in range(3, 15):
            ws.write(r, 0, f'{r - 2}.0', self.formats['cell_center'])
            for c in range(1, 7):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 11: TRAVEL
    # ==========================================
    def _write_travel(self):
        ws = self.workbook.add_worksheet('Travel')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 15)
        ws.set_column('C:C', 20)
        ws.set_column('D:N', 12)

        # Flights section
        ws.merge_range('A1:N1', "Flights", self.formats['header_dark'])

        # Sub-headers
        ws.merge_range('C2:E2', "Booking Info", self.formats['dept_header'])
        ws.merge_range('F2:I2', "Outbound", self.formats['dept_header'])
        ws.merge_range('J2:M2', "Inbound", self.formats['dept_header'])

        headers = ['#', 'Role', 'Name', 'Birthday', 'Frequent Flyer #',
                   'Date', 'Airline', 'Departure', 'Arrival',
                   'Date', 'Airline', 'Departure', 'Arrival', 'Notes']
        for col, h in enumerate(headers):
            ws.write(2, col, h, self.formats['cell_bold'])

        # Standard roles
        roles = ['EP', 'Director', 'Producer', 'DP', 'Talent 1', 'Talent 2']
        for i, role in enumerate(roles):
            row = 3 + i
            ws.write(row, 0, f'{i + 1}.0', self.formats['cell_center'])
            ws.write(row, 1, role, self.formats['cell_normal'])
            for c in range(2, 14):
                ws.write_blank(row, c, None, self.formats['cell_normal'])

        # Lodging section
        lodging_row = 10
        ws.merge_range(f'A{lodging_row}:N{lodging_row}', "Lodging", self.formats['header_dark'])

        lodging_headers = ['#', 'Role', 'Name', 'Hotel', 'Check-In', 'Check-Out', 'Confirmation #', 'Notes']
        for col, h in enumerate(lodging_headers):
            ws.write(lodging_row, col, h, self.formats['cell_bold'])

        for r in range(lodging_row + 1, lodging_row + 8):
            ws.write(r, 0, f'{r - lodging_row}.0', self.formats['cell_center'])
            for c in range(1, 8):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 12: TRAVEL MEMO
    # ==========================================
    def _write_travel_memo(self):
        ws = self.workbook.add_worksheet('Travel Memo')
        ws.set_column('A:Z', 12)

        prod_info = self.data.get('production_info', {})
        client = prod_info.get('client', 'CLIENT')

        ws.merge_range('A1:J1', f"{client} - WEEKLY SCHEDULE", self.formats['header_dark'])

        # Section headers
        ws.write('A3', "Shoot", self.formats['dept_header'])
        ws.write('D3', "Hotel", self.formats['dept_header'])
        ws.write('G3', "Location", self.formats['dept_header'])

        # Add placeholder content
        days = self.data.get('schedule_days', [])
        row = 4
        for day in days:
            ws.write(row, 0, f"Day {day.get('day_number', '')}", self.formats['cell_bold'])
            ws.write(row, 1, day.get('date', 'TBD'), self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 13: WRAP NOTES
    # ==========================================
    def _write_wrap_notes(self):
        ws = self.workbook.add_worksheet('Wrap Notes')
        ws.set_column('A:V', 15)

        prod_info = self.data.get('production_info', {})

        ws.merge_range('A1:V1', "WRAP REPORT", self.formats['header_dark'])

        # Header info
        ws.write('A3', "Job Name:", self.formats['cell_bold'])
        ws.write('B3', prod_info.get('job_name', 'TBD'), self.formats['cell_normal'])
        ws.write('C3', "Producer:", self.formats['cell_bold'])
        ws.write('D3', '', self.formats['cell_normal'])
        ws.write('E3', "UPM:", self.formats['cell_bold'])
        ws.write('F3', '', self.formats['cell_normal'])

        ws.write('A4', "Client:", self.formats['cell_bold'])
        ws.write('B4', prod_info.get('client', 'TBD'), self.formats['cell_normal'])
        ws.write('C4', "Wrap Date:", self.formats['cell_bold'])
        ws.write('D4', '', self.formats['cell_normal'])

        # Wrap notes sections
        sections = ['Equipment Returns', 'Outstanding Payments', 'Final Deliverables', 'Notes']
        row = 6
        for section in sections:
            ws.merge_range(row, 0, row, 5, section, self.formats['dept_header'])
            row += 1
            for _ in range(4):
                for c in range(6):
                    ws.write_blank(row, c, None, self.formats['cell_normal'])
                row += 1
            row += 1


# ==========================================
# TOOL ENTRY POINT
# ==========================================

def _extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in markdown code block (greedy match to handle truncation)
    json_match = re.search(r'```(?:json)?\s*([\s\S]*)', text)
    if json_match:
        json_str = json_match.group(1).strip()
        # Remove closing ``` if present
        json_str = re.sub(r'\s*```\s*$', '', json_str)
    else:
        # Try to find JSON object in the text
        # Look for first { and last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx >= 0 and end_idx > start_idx:
            json_str = text[start_idx:end_idx+1]
        else:
            # Assume the entire response is JSON
            json_str = text.strip()
    
    # First attempt to parse without repair
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[WARN] Initial JSON parse failed, attempting repair: {e}")
        print(f"[WARN] JSON string length: {len(json_str)}")
        
        # Try to repair truncated JSON
        try:
            repaired_json = _repair_truncated_json(json_str)
            print(f"[INFO] Attempting to parse repaired JSON (length: {len(repaired_json)})")
            print(f"[DEBUG] Last 200 chars of repaired JSON: ...{repaired_json[-200:]}")
            return json.loads(repaired_json)
        except json.JSONDecodeError as e2:
            print(f"[ERROR] Failed to parse JSON even after repair: {e2}")
            print(f"[ERROR] JSON string (first 1000 chars): {json_str[:1000]}")
            print(f"[ERROR] JSON string length: {len(json_str)}")
            # Try to find where the error occurred
            if hasattr(e2, 'pos') and e2.pos is not None:
                print(f"[ERROR] Error position: {e2.pos}")
                start_pos = max(0, e2.pos - 200)
                end_pos = min(len(json_str), e2.pos + 200)
                print(f"[ERROR] Context before error ({max(0, start_pos-500)}:{start_pos}): ...{json_str[max(0, start_pos-500):start_pos]}")
                print(f"[ERROR] Context around error ({start_pos}:{end_pos}): {json_str[start_pos:end_pos]}")
                print(f"[ERROR] Context after error ({end_pos}:{min(len(json_str), end_pos+500)}): {json_str[end_pos:min(len(json_str), end_pos+500)]}...")
            raise ValueError(f"Invalid JSON response from LLM: {e2}")


def _repair_truncated_json(json_str: str) -> str:
    """Try to repair truncated JSON by closing open structures.
    
    Handles cases where JSON is truncated mid-structure, including:
    - Unclosed strings
    - Incomplete field values  
    - Unclosed objects/arrays
    """
    json_str = json_str.strip()
    
    # Track state as we iterate through the string
    in_string = False
    escape_next = False
    brace_depth = 0
    bracket_depth = 0
    
    # First pass: count braces and brackets, track string state
    for i, char in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"':
            in_string = not in_string
        elif not in_string:
            if char == '{':
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
            elif char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
    
    # Remove trailing whitespace
    json_str = json_str.rstrip()
    
    # If we're in a string at the end, close it
    if in_string:
        json_str += '"'
        in_string = False  # Update state after closing string
    
    # Re-count depths after potential string closure
    # Use a smarter approach: find what's actually open at the END by scanning backwards
    # Scan from the end to find actual open structures
    # This is more accurate than global count for truncated JSON
    end_brace_depth = 0
    end_bracket_depth = 0
    scan_in_string = False
    scan_escape = False
    
    # Work backwards from the end
    i = len(json_str) - 1
    while i >= 0:
        char = json_str[i]
        if scan_escape:
            scan_escape = False
            i -= 1
            continue
        if char == '\\' and i > 0:
            # Check if this is an escape sequence
            scan_escape = True
            i -= 1
            continue
        if char == '"':
            scan_in_string = not scan_in_string
        elif not scan_in_string:
            if char == '}':
                end_brace_depth += 1
            elif char == '{':
                if end_brace_depth > 0:
                    end_brace_depth -= 1
                else:
                    # Found an unclosed opening brace
                    break
            elif char == ']':
                end_bracket_depth += 1
            elif char == '[':
                if end_bracket_depth > 0:
                    end_bracket_depth -= 1
                else:
                    # Found an unclosed opening bracket
                    break
        i -= 1
    
    # Use the more accurate depth counting
    brace_depth = end_brace_depth
    bracket_depth = end_bracket_depth
    
    # Check if we have an incomplete field (colon without complete value)
    # Look for pattern: "key": "incomplete or "key": incomplete
    # We need to find the last colon and see if what follows is complete
    last_colon_pos = json_str.rfind(':')
    if last_colon_pos > 0 and not in_string:
        after_colon = json_str[last_colon_pos + 1:].strip()
        # If after colon is empty or starts a string that's not closed, complete it
        if not after_colon:
            # No value after colon - add null
            json_str += 'null'
        elif after_colon.startswith('"') and not after_colon.endswith('"'):
            # String started but not closed - should already be handled above
            pass
        elif after_colon and not any(after_colon.startswith(p) for p in ['"', '[', '{', 'null', 'true', 'false', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
            # Value looks incomplete - this shouldn't happen normally, but if it does, add null
            # Actually, if we get here, the string closing above should have handled it
            pass
    
    # Remove trailing comma if present
    json_str = json_str.rstrip()
    if json_str.endswith(','):
        json_str = json_str[:-1].rstrip()
    
    # Close open objects first (they might be inside arrays)
    # Objects need to be closed before arrays that contain them
    if brace_depth > 0:
        json_str += '\n' + '}' * brace_depth
    
    # Close open arrays
    if bracket_depth > 0:
        json_str += '\n' + ']' * bracket_depth
    
    # Final cleanup: remove any trailing comma again after closing structures
    json_str = json_str.rstrip()
    if json_str.endswith(','):
        json_str = json_str[:-1].rstrip()
    
    return json_str


def _get_api_key() -> str:
    """Get Gemini API key from environment variables."""
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError(
            "Missing API key. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
        )
    return api_key


def run_tool(
    prompt: str,
    attached_file_content: str = None,
    enrich: bool = True,
    progress_callback: Optional[Callable[[str, int, str], None]] = None
) -> dict:
    """
    Execute the Epitome production workbook generation pipeline.

    1. Uses Gemini LLM with EPITOME_EXTRACTION_SYSTEM_PROMPT to parse
       the user prompt and optional file content into structured JSON.
    2. Enriches data with external APIs (location, weather, company info).
    3. Passes the enriched JSON to EpitomeWorkbookGenerator.
    4. Returns the enriched data and workbook path.

    Args:
        prompt: Natural language request (e.g., "Create call sheets for a 5 day shoot for Google")
        attached_file_content: Optional CSV/text content of crew list or schedule
        enrich: Whether to enrich data with external APIs (default: True)
        progress_callback: Optional callback for progress updates (stage_id, percent, message)

    Returns:
        Dict with 'workbook_path' and 'data' (enriched production data for dashboard)

    Raises:
        ValueError: If API key is missing
        Exception: If LLM call or JSON parsing fails
    """
    def emit(stage_id: str, percent: int, message: str):
        """Emit progress update."""
        if progress_callback:
            progress_callback(stage_id, percent, message)
        print(message)

    # Stage 1: Analyzing file (if provided)
    if attached_file_content:
        emit("analyzing_file", 5, "Analyzing uploaded file...")
        # Count content length to estimate processing time
        content_length = len(attached_file_content) if attached_file_content else 0
        if content_length > 1000:
            emit("analyzing_file", 8, f"Processing file content ({content_length:,} characters)...")
        emit("analyzing_file", 12, "File content prepared for extraction")

    # Stage 2: Understanding prompt
    emit("understanding_prompt", 18, "Understanding prompt...")

    # Get API key and initialize client
    api_key = _get_api_key()
    client = genai.Client(api_key=api_key)

    # Build user message
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Handle empty prompt - if no prompt but file is provided, use default message
    if prompt and prompt.strip():
        user_message = f"Today's date is {today}.\n\nUser request: {prompt}"
    else:
        # No prompt provided - extract information from the file only
        user_message = f"Today's date is {today}.\n\nExtract production information from the attached file and create call sheets."

    if attached_file_content:
        user_message += f"\n\nAttached file content:\n{attached_file_content}"

    # Stage 3: Extracting data with LLM
    emit("extracting_data", 25, "Sending to AI for extraction...")
    emit("extracting_data", 35, "AI is analyzing and extracting production data...")
    
    # Show progress during API call (this is where most time is spent)
    if attached_file_content and len(attached_file_content) > 5000:
        emit("extracting_data", 40, "Processing large file content with AI...")

    # Use system instruction for better compatibility
    from google.genai import types
    
    config = types.GenerateContentConfig(
        temperature=0.2,
        maxOutputTokens=16384,  # Increased to handle very large responses with many crew members
        systemInstruction=EPITOME_EXTRACTION_SYSTEM_PROMPT,
    )
    
    emit("extracting_data", 50, "Calling Gemini API...")
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",  # Use available model
        contents=user_message,
        config=config
    )
    
    emit("extracting_data", 65, "Received response from AI, parsing...")

    emit("extracting_data", 60, "Parsing extracted data...")

    # Extract JSON from response - handle various response scenarios
    try:
        response_text = response.text
    except Exception as text_error:
        # Some responses may not have a .text property
        print(f"[ERROR] Could not get response.text: {text_error}")
        # Try to get text from candidates
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
                else:
                    raise ValueError(f"No text in response content: {candidate.content}")
            else:
                raise ValueError(f"No content in response candidate: {candidate}")
        else:
            raise ValueError(f"Could not extract text from response: {response}")

    # Check if response is empty
    if not response_text or not response_text.strip():
        print(f"[ERROR] Empty response from Gemini API")
        print(f"[DEBUG] Full response object: {response}")
        if hasattr(response, 'candidates'):
            print(f"[DEBUG] Candidates: {response.candidates}")
        if hasattr(response, 'prompt_feedback'):
            print(f"[DEBUG] Prompt feedback: {response.prompt_feedback}")
        raise ValueError("Gemini API returned an empty response. Please try again.")

    # Debug: Log the response (first 500 chars)
    print(f"\n[DEBUG] Gemini response (first 500 chars): {response_text[:500]}")

    try:
        extracted_data = _extract_json_from_response(response_text)
        print(f"[DEBUG] Extracted data keys: {list(extracted_data.keys())}")
        print(f"[DEBUG] Job name: {extracted_data.get('production_info', {}).get('job_name', 'N/A')}")
        print(f"[DEBUG] Crew count: {len(extracted_data.get('crew_list', []))}")
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        print(f"[ERROR] Response text: {response_text[:1000]}")
        raise
    
    emit("extracting_data", 70, "Data extraction complete")

    # Stage 4-6: Enrich data with external APIs (sub-progress in enrichment.py)
    if enrich:
        enriched_data = enrich_production_data(extracted_data, progress_callback=progress_callback)
    else:
        enriched_data = extracted_data
    
    # Debug: Verify data before generating workbook
    print(f"[DEBUG] Before workbook generation:")
    print(f"[DEBUG]   Job name: {enriched_data.get('production_info', {}).get('job_name', 'N/A')}")
    print(f"[DEBUG]   Job number: {enriched_data.get('production_info', {}).get('job_number', 'N/A')}")
    print(f"[DEBUG]   Crew count: {len(enriched_data.get('crew_list', []))}")
    print(f"[DEBUG]   Schedule days: {len(enriched_data.get('schedule_days', []))}")

    # Stage 7: Generate workbook
    emit("generating", 90, "Generating workbook...")

    output_file = "Epitome_Production_Workbook.xlsx"
    generator = EpitomeWorkbookGenerator(data=enriched_data, output_filename=output_file)
    final_path = generator.generate()

    # Stage 8: Complete
    emit("complete", 100, "Complete!")

    return {
        'workbook_path': final_path,
        'data': enriched_data
    }


if __name__ == "__main__":
    # Test Run
    result = run_tool("Create call sheets for a 5 day shoot for Google starting next Monday")
    print(f"\nWorkbook: {result['workbook_path']}")
    print(f"\nEnriched Data Keys: {list(result['data'].keys())}")
    if result['data'].get('client_info'):
        print(f"Client Logo: {result['data']['client_info'].get('logo_url')}")
