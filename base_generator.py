"""
Base Generator - Common functionality for all diagram generators
"""

import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

# Try relative import first, then absolute
try:
    from .mermaid_utils import MermaidUtils
except ImportError:
    from mermaid_utils import MermaidUtils


class BaseGenerator:
    """Base class with common functionality for all generators"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info(f"[{self.__class__.__name__}] Initialized")
        self.utils = MermaidUtils()

    def _build_type_lookup(self, xml_export):
        """Build complete type lookup from XML export"""
        type_lookup = {}

        if xml_export:
            # Add enums
            if hasattr(xml_export, 'enums'):
                for enum in xml_export.enums:
                    type_lookup[enum.name] = ('enum', enum)
                    type_lookup[enum.name.lower()] = ('enum', enum)

            # Add structures
            if hasattr(xml_export, 'structures'):
                for struct in xml_export.structures:
                    type_lookup[struct.name] = ('structure', struct)
                    type_lookup[struct.name.lower()] = ('structure', struct)

            # Add unions
            if hasattr(xml_export, 'unions'):
                for union in xml_export.unions:
                    type_lookup[union.name] = ('union', union)
                    type_lookup[union.name.lower()] = ('union', union)

            self.logger.info(f"[{self.__class__.__name__}] Built type lookup with {len(type_lookup)//2} unique types")

        return type_lookup

    def _find_all_related_types(self, start_type, type_lookup, visited=None):
        """Recursively find all related types"""
        if visited is None:
            visited = set()

        type_name = start_type.name
        if type_name in visited:
            return visited

        visited.add(type_name)

        # If it's a structure or union, check all members
        if hasattr(start_type, 'members'):
            for member in start_type.members:
                member_type = member.type
                member_type_lower = member.type.lower()

                # Skip basic types
                if self._is_basic_type(member_type):
                    continue

                # Check if member type exists in lookup
                if member_type in type_lookup or member_type_lower in type_lookup:
                    type_key = member_type if member_type in type_lookup else member_type_lower
                    type_info = type_lookup.get(type_key)

                    if type_info:
                        type_obj = type_info[1]
                        self._find_all_related_types(type_obj, type_lookup, visited)

        return visited

    def _is_basic_type(self, type_name):
        """Check if a type is a basic type"""
        type_upper = type_name.upper()
        return type_upper in {'INT', 'BOOL', 'REAL', 'DINT', 'LINT', 'SINT', 'USINT',
                             'UINT', 'UDINT', 'ULINT', 'BYTE', 'WORD', 'DWORD', 'LWORD',
                             'STRING', 'CHAR', 'WCHAR', 'TIME', 'DATE', 'DT', 'TOD'}

    def _get_safe_node_id(self, name: str, counter: int = None) -> str:
        """Get a safe node ID using MermaidUtils"""
        return self.utils.create_safe_node_id(name, counter)

    def _sanitize_label(self, text: str) -> str:
        """Sanitize label text using MermaidUtils"""
        return self.utils.sanitize_label_text(text)

    def _save_file(self, name: str, output_dir: Path, html: str, item_type: str) -> str:
        """Save HTML file and return path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.html"
        filepath = output_dir / filename

        self.logger.info(f"[{self.__class__.__name__}] Saving {item_type} to: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(filepath)