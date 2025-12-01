"""
ER Diagram Generator - Uses Mermaid erDiagram syntax
"""

import logging
import traceback
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from base_generator import BaseGenerator

class ERDiagramGenerator:
    """Generates Mermaid ER diagrams"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("[ERDiagramGenerator] Initialized")

    def generate_for_structure(self, structure, xml_export, output_dir: Path) -> str:
        """Generate ER diagram for a structure"""
        try:
            self.logger.info(f"[ERDiagramGenerator] Generating ER diagram for structure: {structure.name}")

            # Build type lookup
            type_lookup = self._build_type_lookup(xml_export)

            # Find all related types
            all_types = self._find_all_related_types(structure, type_lookup)

            # Generate ER diagram
            mermaid_code = self._create_structure_erdiagram(structure, all_types, type_lookup)

            # Create HTML
            html = self._create_html_page(structure.name, "Structure", mermaid_code, all_types, type_lookup)

            # Save file
            return self._save_file(structure.name, output_dir, html, "structure")

        except Exception as e:
            self.logger.error(f"[ERDiagramGenerator] Error: {str(e)}", exc_info=True)
            return ""

    # Add other methods and helpers