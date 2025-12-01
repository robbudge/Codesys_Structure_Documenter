"""
Class Diagram Generator - Uses Mermaid classDiagram syntax
"""

import logging
import traceback
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from base_generator import BaseGenerator

class ClassDiagramGenerator:
    """Generates Mermaid class diagrams"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("[ClassDiagramGenerator] Initialized")

    def generate_for_structure(self, structure, xml_export, output_dir: Path) -> str:
        """Generate class diagram for a structure"""
        try:
            self.logger.info(f"[ClassDiagramGenerator] Generating class diagram for structure: {structure.name}")

            # Build type lookup
            type_lookup = self._build_type_lookup(xml_export)

            # Find all related types
            all_types = self._find_all_related_types(structure, type_lookup)

            # Generate class diagram
            mermaid_code = self._create_structure_classdiagram(structure, all_types, type_lookup)

            # Create HTML
            html = self._create_html_page(structure.name, "Structure", mermaid_code, all_types, type_lookup)

            # Save file
            return self._save_file(structure.name, output_dir, html, "structure")

        except Exception as e:
            self.logger.error(f"[ClassDiagramGenerator] Error: {str(e)}", exc_info=True)
            return ""

    # Add other methods and helpers