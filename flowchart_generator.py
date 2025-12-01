"""
Flowchart Generator - Uses Mermaid flowchart syntax with vertical/horizontal layout
"""

import logging
import traceback
from typing import Dict, Any
from pathlib import Path

from base_generator import BaseGenerator
from html_templates import HTMLTemplates


class FlowchartGenerator(BaseGenerator):
    """Generates Mermaid flowchart diagrams with proper vertical/horizontal layout"""

    def __init__(self, logger=None):
        # Call parent constructor
        super().__init__(logger)
        self.logger.info("[FlowchartGenerator] Initialized")
        self.node_counter = 0
        self.templates = HTMLTemplates()

    def generate_for_structure(self, structure, xml_export, output_dir: Path) -> str:
        """Generate flowchart for a structure"""
        try:
            self.logger.info(f"[FlowchartGenerator] Generating flowchart for structure: {structure.name}")

            # Build type lookup
            type_lookup = self._build_type_lookup(xml_export)

            # Generate flowchart
            mermaid_code = self._create_type_flowchart(structure, type_lookup)

            # Validate Mermaid code
            if not self.utils.validate_mermaid_code(mermaid_code, self.logger):
                self.logger.warning("[FlowchartGenerator] Mermaid code validation failed")

            # Create content for HTML template
            legend = self.templates.create_flowchart_legend()
            details = self.templates.create_type_details_table(structure, "Structure Members")

            # Create HTML using template
            html = self.templates.create_base_page(
                title=f"{structure.name} - Structure Flowchart",
                mermaid_code=mermaid_code,
                diagram_type="Flowchart Diagram",
                content_before=legend,
                content_after=details
            )

            # Save file
            return self._save_file(structure.name, output_dir, html, "structure")

        except Exception as e:
            self.logger.error(f"[FlowchartGenerator] Error: {str(e)}", exc_info=True)
            return ""

    def generate_for_union(self, union, xml_export, output_dir: Path) -> str:
        """Generate flowchart for a union"""
        try:
            self.logger.info(f"[FlowchartGenerator] Generating flowchart for union: {union.name}")

            # Build type lookup
            type_lookup = self._build_type_lookup(xml_export)

            # Generate flowchart
            mermaid_code = self._create_type_flowchart(union, type_lookup)

            # Validate Mermaid code
            if not self.utils.validate_mermaid_code(mermaid_code, self.logger):
                self.logger.warning("[FlowchartGenerator] Mermaid code validation failed")

            # Create content for HTML template
            legend = self.templates.create_flowchart_legend()
            details = self.templates.create_type_details_table(union, "Union Members")

            # Create HTML using template
            html = self.templates.create_base_page(
                title=f"{union.name} - Union Flowchart",
                mermaid_code=mermaid_code,
                diagram_type="Flowchart Diagram",
                content_before=legend,
                content_after=details
            )

            # Save file
            return self._save_file(union.name, output_dir, html, "union")

        except Exception as e:
            self.logger.error(f"[FlowchartGenerator] Error: {str(e)}", exc_info=True)
            return ""

    def generate_for_enum(self, enum, output_dir: Path) -> str:
        """Generate flowchart for an enum"""
        try:
            self.logger.info(f"[FlowchartGenerator] Generating flowchart for enum: {enum.name}")

            # Generate enum flowchart
            mermaid_code = self._create_enum_flowchart(enum)

            # Validate Mermaid code
            if not self.utils.validate_mermaid_code(mermaid_code, self.logger):
                self.logger.warning("[FlowchartGenerator] Mermaid code validation failed")

            # Create content for HTML template
            enum_table = self.templates.create_enum_table(enum)

            # Create HTML using template
            html = self.templates.create_base_page(
                title=f"{enum.name} - Enumeration Flowchart",
                mermaid_code=mermaid_code,
                diagram_type="Enumeration Diagram",
                content_after=enum_table
            )

            # Save file
            return self._save_file(enum.name, output_dir, html, "enum")

        except Exception as e:
            self.logger.error(f"[FlowchartGenerator] Error: {str(e)}", exc_info=True)
            return ""

    def _create_type_flowchart(self, item, type_lookup):
        """Create flowchart for a structure or union following vertical/horizontal rules"""
        self.node_counter = 0  # Reset counter
        lines = ["flowchart TD"]
        lines.append("")

        # Define styles
        lines.append("    %% Node styles")
        lines.append("    classDef structure fill:#e1f5fe,stroke:#01579b,stroke-width:2px")
        lines.append("    classDef union fill:#f3e5f5,stroke:#4a148c,stroke-width:2px")
        lines.append("    classDef enum fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px")
        lines.append("    classDef basic fill:#f5f5f5,stroke:#616161,stroke-width:1px")
        lines.append("    classDef member fill:#ffffff,stroke:#90a4ae,stroke-width:1px")
        lines.append("")

        # Start with main type - USE SANITIZED ID
        main_node_id = self._get_safe_node_id(item.name, 1)

        # Create main type node
        type_label = self._create_type_label(item)
        lines.append(f'    {main_node_id}["{type_label}"]')
        lines.append(f'    class {main_node_id} {"union" if getattr(item, "is_union", False) else "structure"}')
        lines.append("")

        # Track processed types to avoid infinite recursion
        processed_types = set()

        # Create flowchart recursively
        self._add_members_flowchart(item, main_node_id, lines, type_lookup, processed_types, 0)

        result = '\n'.join(lines)

        # Log generated code for debugging
        self.logger.debug(f"[FlowchartGenerator] Generated flowchart code ({len(result)} chars)")

        return result

    def _add_members_flowchart(self, item, parent_node_id, lines, type_lookup, processed_types, depth):
        """Recursively add members to flowchart"""
        if item.name in processed_types:
            # Already processed this type, just link to it
            type_node_id = self._get_safe_node_id(item.name)
            lines.append(f'    {parent_node_id} -.-> {type_node_id}')
            return

        processed_types.add(item.name)

        if not hasattr(item, 'members') or not item.members:
            return

        # Sort members: basic types first, then complex types
        basic_members = []
        complex_members = []

        for member in item.members:
            if self._is_basic_type(member.type):
                basic_members.append(member)
            else:
                complex_members.append(member)

        # Add basic members first (vertical)
        current_parent = parent_node_id
        for member in basic_members:
            self.node_counter += 1
            member_node_id = self._get_safe_node_id(f"{item.name}_{member.name}", self.node_counter)
            member_label = self._create_member_label(member)
            lines.append(f'    {member_node_id}["{member_label}"]')
            lines.append(f'    class {member_node_id} member')
            lines.append(f'    {current_parent} --> {member_node_id}')
            current_parent = member_node_id

        # Add complex members (horizontal branches)
        for member in complex_members:
            self.node_counter += 1
            member_node_id = self._get_safe_node_id(f"{item.name}_{member.name}", self.node_counter)
            member_label = self._create_member_label(member)

            # Member node
            lines.append(f'    {member_node_id}["{member_label}"]')
            lines.append(f'    class {member_node_id} member')
            lines.append(f'    {parent_node_id} --> {member_node_id}')

            # Check if member type exists in lookup
            member_type_lower = member.type.lower()
            if member_type_lower in type_lookup:
                type_info = type_lookup[member_type_lower]
                type_category, type_obj = type_info

                # Create type node (horizontal) - USE SANITIZED ID
                self.node_counter += 1
                type_node_id = self._get_safe_node_id(member.type, self.node_counter)

                # Only create if not already created (check if ID exists in lines)
                if not any(line.strip().startswith(f'{type_node_id}["') for line in lines):
                    type_label = self._create_type_label(type_obj)
                    lines.append(f'    {type_node_id}["{type_label}"]')

                    # Set style based on type category
                    if type_category == 'enum':
                        lines.append(f'    class {type_node_id} enum')
                    elif type_category == 'structure':
                        lines.append(f'    class {type_node_id} structure')
                    elif type_category == 'union':
                        lines.append(f'    class {type_node_id} union')

                # Connect member to type (horizontal)
                lines.append(f'    {member_node_id} --> {type_node_id}')

                # Recursively add members of this type
                if type_category in ['structure', 'union']:
                    self._add_members_flowchart(type_obj, type_node_id, lines, type_lookup, processed_types, depth + 1)
            else:
                # Type not found, show as unknown - SANITIZE THE TYPE NAME
                self.node_counter += 1
                sanitized_type = self._sanitize_label(member.type)
                type_node_id = self._get_safe_node_id(f"unknown_{member.type}", self.node_counter)
                type_label = f"<b>{sanitized_type}</b><br><i>Unknown Type</i>"
                lines.append(f'    {type_node_id}["{type_label}"]')
                lines.append(f'    class {type_node_id} basic')
                lines.append(f'    {member_node_id} --> {type_node_id}')

    def _create_enum_flowchart(self, enum):
        """Create flowchart for an enum"""
        lines = ["flowchart TD"]
        lines.append("")

        # Define enum style
        lines.append("    classDef enum fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px")
        lines.append("    classDef enumvalue fill:#ffffff,stroke:#81c784,stroke-width:1px")
        lines.append("")

        # Enum node - USE SANITIZED ID
        enum_id = self._get_safe_node_id(enum.name, 1)
        enum_label = f"<b>{self._sanitize_label(enum.name)}</b><br><i>Enumeration</i><hr style='margin: 2px 0;'>{len(enum.values)} values"
        lines.append(f'    {enum_id}["{enum_label}"]')
        lines.append(f'    class {enum_id} enum')
        lines.append("")

        # Enum values (vertical layout)
        prev_node = enum_id
        for i, value in enumerate(enum.values[:10]):  # Limit to 10 values for readability
            self.node_counter += 1
            value_id = self._get_safe_node_id(f"{enum.name}_{value.name}", self.node_counter)
            value_label = f"{self._sanitize_label(value.name)} = {value.value}"
            lines.append(f'    {value_id}["{value_label}"]')
            lines.append(f'    class {value_id} enumvalue')
            lines.append(f'    {prev_node} --> {value_id}')
            prev_node = value_id

        if len(enum.values) > 10:
            self.node_counter += 1
            more_id = self._get_safe_node_id(f"{enum.name}_more", self.node_counter)
            lines.append(f'    {more_id}["... and {len(enum.values) - 10} more"]')
            lines.append(f'    class {more_id} enumvalue')
            lines.append(f'    {prev_node} --> {more_id}')

        return '\n'.join(lines)

    def _create_type_label(self, item):
        """Create HTML label for a type node"""
        type_name = self._sanitize_label(item.name)
        is_union = getattr(item, 'is_union', False)
        member_count = len(item.members) if hasattr(item, 'members') else 0

        label = f"<b>{type_name}</b><br>"
        label += f"<i>{'Union' if is_union else 'Structure'}</i><br>"
        label += f"<hr style='margin: 2px 0;'>{member_count} members"

        return label

    def _create_member_label(self, member):
        """Create HTML label for a member node"""
        member_name = self._sanitize_label(member.name)
        member_type = self._sanitize_label(member.type)

        label = f"<b>{member_name}</b><br>"
        label += f"<i>{member_type}</i>"

        # Add initial value if present
        if hasattr(member, 'initial_value') and member.initial_value is not None:
            label += f"<br>= {self._sanitize_label(str(member.initial_value))}"

        return label