"""
Flowchart Generator - Standalone version with corrected member layout
"""

import logging
import traceback
import re
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class FlowchartGenerator:
    """Generates Mermaid flowchart diagrams with proper vertical/horizontal layout"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("[FlowchartGenerator] Initialized")
        self.node_counter = 0

    # ====== Helper methods ======

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

            self.logger.info(f"[FlowchartGenerator] Built type lookup with {len(type_lookup)//2} unique types")

        return type_lookup

    def _is_basic_type(self, type_name):
        """Check if a type is a basic type"""
        type_upper = type_name.upper()
        return type_upper in {'INT', 'BOOL', 'REAL', 'DINT', 'LINT', 'SINT', 'USINT',
                             'UINT', 'UDINT', 'ULINT', 'BYTE', 'WORD', 'DWORD', 'LWORD',
                             'STRING', 'CHAR', 'WCHAR', 'TIME', 'DATE', 'DT', 'TOD'}

    def _sanitize_node_id(self, name: str) -> str:
        """Sanitize a string to be a valid Mermaid node ID."""
        if not name:
            return "node"

        # Replace problematic characters with underscores
        sanitized = str(name)
        sanitized = re.sub(r'[()\[\]{}<>]', '_', sanitized)
        sanitized = re.sub(r'[#@$%^&*+=|\\/:";\',.?`~]', '_', sanitized)
        sanitized = sanitized.replace(' ', '_').replace('-', '_')
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')

        if sanitized and not sanitized[0].isalpha():
            sanitized = 'node_' + sanitized

        return sanitized or 'node'

    def _sanitize_label_text(self, text: str) -> str:
        """Sanitize text for Mermaid labels."""
        if not text:
            return ""

        sanitized = text.replace('"', '&quot;').replace("'", "&apos;").replace('\n', '<br>')
        return sanitized

    def _get_safe_node_id(self, name: str, counter: int = None) -> str:
        """Get a safe node ID"""
        safe_id = self._sanitize_node_id(name)
        if counter is not None:
            safe_id = f"{safe_id}_{counter}"
        return safe_id

    # ====== Main generator methods ======

    def generate_for_structure(self, structure, xml_export, output_dir: Path) -> str:
        """Generate flowchart for a structure"""
        try:
            self.logger.info(f"[FlowchartGenerator] Generating flowchart for structure: {structure.name}")

            # Build type lookup
            type_lookup = self._build_type_lookup(xml_export)

            # Generate flowchart
            mermaid_code = self._create_type_flowchart(structure, type_lookup)

            # Create HTML
            html = self._create_html_page(structure.name, "Structure", mermaid_code, structure, type_lookup)

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

            # Create HTML
            html = self._create_html_page(union.name, "Union", mermaid_code, union, type_lookup)

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

            # Create HTML
            html = self._create_enum_html_page(enum, mermaid_code)

            # Save file
            return self._save_file(enum.name, output_dir, html, "enum")

        except Exception as e:
            self.logger.error(f"[FlowchartGenerator] Error: {str(e)}", exc_info=True)
            return ""

    # ====== Flowchart creation methods ======

    def _create_type_flowchart(self, item, type_lookup):
        """Create flowchart for a structure or union"""
        self.node_counter = 0
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

        # Start with main type
        self.node_counter += 1
        main_node_id = self._get_safe_node_id(item.name, self.node_counter)

        # Create main type node
        type_label = self._create_type_label(item)
        lines.append(f'    {main_node_id}["{type_label}"]')
        lines.append(f'    class {main_node_id} {"union" if getattr(item, "is_union", False) else "structure"}')
        lines.append("")

        # Track processed types
        processed_types = set()

        # Create flowchart recursively
        self._add_members_flowchart(item, main_node_id, lines, type_lookup, processed_types)

        result = '\n'.join(lines)
        self.logger.debug(f"[FlowchartGenerator] Generated flowchart code ({len(result)} chars)")

        return result

    def _add_members_flowchart(self, item, parent_node_id, lines, type_lookup, processed_types):
        """Recursively add members to flowchart - FIXED VERSION"""
        if item.name in processed_types:
            # Already processed, just link
            type_node_id = self._get_safe_node_id(item.name)
            lines.append(f'    {parent_node_id} -.-> {type_node_id}')
            return

        processed_types.add(item.name)

        if not hasattr(item, 'members') or not item.members:
            return

        # Separate members by type
        basic_members = []
        complex_members = []

        for member in item.members:
            if self._is_basic_type(member.type):
                basic_members.append(member)
            else:
                complex_members.append(member)

        # Add basic members in a vertical chain
        if basic_members:
            current_parent = parent_node_id
            for member in basic_members:
                self.node_counter += 1
                member_node_id = self._get_safe_node_id(f"{item.name}_{member.name}", self.node_counter)
                member_label = self._create_member_label(member)

                lines.append(f'    {member_node_id}["{member_label}"]')
                lines.append(f'    class {member_node_id} member')
                lines.append(f'    {current_parent} --> {member_node_id}')
                current_parent = member_node_id

        # Add complex members as direct branches from the parent
        for member in complex_members:
            self.node_counter += 1
            member_node_id = self._get_safe_node_id(f"{item.name}_{member.name}", self.node_counter)
            member_label = self._create_member_label(member)

            # Member node connects DIRECTLY to parent (not in chain)
            lines.append(f'    {member_node_id}["{member_label}"]')
            lines.append(f'    class {member_node_id} member')
            lines.append(f'    {parent_node_id} --> {member_node_id}')

            # Handle the member's type
            self._add_member_type_flowchart(member, member_node_id, lines, type_lookup, processed_types)

    def _add_member_type_flowchart(self, member, member_node_id, lines, type_lookup, processed_types):
        """Add the type node for a complex member"""
        member_type_lower = member.type.lower()

        if member_type_lower in type_lookup:
            type_info = type_lookup[member_type_lower]
            type_category, type_obj = type_info

            # Create type node
            self.node_counter += 1
            type_node_id = self._get_safe_node_id(member.type, self.node_counter)

            # Only create if not already created
            if not any(line.strip().startswith(f'{type_node_id}["') for line in lines):
                type_label = self._create_type_label(type_obj)
                lines.append(f'    {type_node_id}["{type_label}"]')

                # Set style
                if type_category == 'enum':
                    lines.append(f'    class {type_node_id} enum')
                elif type_category == 'structure':
                    lines.append(f'    class {type_node_id} structure')
                elif type_category == 'union':
                    lines.append(f'    class {type_node_id} union')

            # Connect member to type
            lines.append(f'    {member_node_id} --> {type_node_id}')

            # Recursively add members of this type
            if type_category in ['structure', 'union']:
                self._add_members_flowchart(type_obj, type_node_id, lines, type_lookup, processed_types)
        else:
            # Unknown type
            self.node_counter += 1
            sanitized_type = self._sanitize_label_text(member.type)
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

        # Enum node
        self.node_counter = 1
        enum_id = self._get_safe_node_id(enum.name, self.node_counter)
        enum_label = f"<b>{self._sanitize_label_text(enum.name)}</b><br><i>Enumeration</i><hr style='margin: 2px 0;'>{len(enum.values)} values"
        lines.append(f'    {enum_id}["{enum_label}"]')
        lines.append(f'    class {enum_id} enum')
        lines.append("")

        # Enum values
        prev_node = enum_id
        for i, value in enumerate(enum.values[:10]):
            self.node_counter += 1
            value_id = self._get_safe_node_id(f"{enum.name}_{value.name}", self.node_counter)
            value_label = f"{self._sanitize_label_text(value.name)} = {value.value}"
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

    # ====== Label creation methods ======

    def _create_type_label(self, item):
        """Create HTML label for a type node"""
        type_name = self._sanitize_label_text(item.name)
        is_union = getattr(item, 'is_union', False)
        member_count = len(item.members) if hasattr(item, 'members') else 0

        label = f"<b>{type_name}</b><br>"
        label += f"<i>{'Union' if is_union else 'Structure'}</i><br>"
        label += f"<hr style='margin: 2px 0;'>{member_count} members"

        return label

    def _create_member_label(self, member):
        """Create HTML label for a member node"""
        member_name = self._sanitize_label_text(member.name)
        member_type = self._sanitize_label_text(member.type)

        label = f"<b>{member_name}</b><br>"
        label += f"<i>{member_type}</i>"

        if hasattr(member, 'initial_value') and member.initial_value is not None:
            label += f"<br>= {self._sanitize_label_text(str(member.initial_value))}"

        return label

    # ====== HTML creation methods ======

    def _create_html_page(self, name: str, item_type: str, mermaid_code: str, item, type_lookup):
        """Create HTML page for the flowchart"""
        # Create type details table
        details_html = ""
        if hasattr(item, 'members'):
            rows = ""
            for member in item.members:
                desc = getattr(member, 'description', '') or ''
                initial = getattr(member, 'initial_value', '')
                initial_text = f" = {initial}" if initial not in [None, ''] else ""

                rows += f"<tr><td>{member.name}</td><td>{member.type}{initial_text}</td><td>{desc}</td></tr>"

            details_html = f"""
        <div class="type-details">
            <h3>Type Details</h3>
            <table>
                <thead>
                    <tr><th>Member</th><th>Type</th><th>Description</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>"""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{name} - {item_type} Flowchart</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        }});
    </script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4A90E2; padding-bottom: 10px; }}
        .mermaid {{ margin: 20px 0; background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; min-height: 600px; }}
        pre {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: monospace; }}
        .note {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        .type-details {{ margin: 20px 0; }}
        .type-details table {{ width: 100%; border-collapse: collapse; }}
        .type-details th {{ background: #4A90E2; color: white; padding: 10px; text-align: left; }}
        .type-details td {{ padding: 8px 10px; border-bottom: 1px solid #ddd; }}
        .type-details tr:nth-child(even) {{ background: #f9f9f9; }}
        
        /* Legend */
        .legend {{ display: flex; flex-wrap: wrap; gap: 15px; margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 3px; border: 1px solid #ccc; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{name} - {item_type} Flowchart Diagram</h1>
        
        <div class="note">
            <strong>Diagram Rules:</strong><br>
            • <strong>Vertical (↓)</strong>: Members step down from their parent type<br>
            • <strong>Horizontal (→)</strong>: Complex types branch across from their member<br>
            • <strong>Basic types</strong> (INT, BOOL, etc.) stay in vertical chain<br>
            • <strong>Complex types</strong> (structures, unions, enums) branch horizontally
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #e1f5fe; border-color: #01579b;"></div>
                <span>Structure</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #f3e5f5; border-color: #4a148c;"></div>
                <span>Union</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #e8f5e8; border-color: #1b5e20;"></div>
                <span>Enumeration</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffffff; border-color: #90a4ae;"></div>
                <span>Member</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #f5f5f5; border-color: #616161;"></div>
                <span>Basic/Unknown Type</span>
            </div>
        </div>
        
        <div class="mermaid">
{mermaid_code}
        </div>
        
        {details_html}
        
        <h2>Mermaid Source Code</h2>
        <pre>
{mermaid_code}
        </pre>
        
        <p><small>Generated by Codesys XML Documentation Generator • Using Mermaid v10.6.1</small></p>
    </div>
</body>
</html>"""
        return html

    def _create_enum_html_page(self, enum, mermaid_code: str) -> str:
        """Create HTML page for enum flowchart"""
        # Create enum values table
        values_html = ""
        if hasattr(enum, 'values'):
            rows = ""
            for i, value in enumerate(enum.values, 1):
                desc = getattr(value, 'description', '') or ''
                rows += f"<tr><td>{i}</td><td>{value.name}</td><td>{value.value}</td><td>{desc}</td></tr>"

            values_html = f"""
        <div class="type-details">
            <h3>Enumeration Values ({len(enum.values)})</h3>
            <table>
                <thead>
                    <tr><th>#</th><th>Name</th><th>Value</th><th>Description</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>"""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{enum.name} - Enumeration Flowchart</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        }});
    </script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4A90E2; padding-bottom: 10px; }}
        .mermaid {{ margin: 20px 0; background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; min-height: 400px; }}
        pre {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: monospace; }}
        .type-details {{ margin: 20px 0; }}
        .type-details table {{ width: 100%; border-collapse: collapse; }}
        .type-details th {{ background: #4A90E2; color: white; padding: 10px; text-align: left; }}
        .type-details td {{ padding: 8px 10px; border-bottom: 1px solid #ddd; }}
        .type-details tr:nth-child(even) {{ background: #f9f9f9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{enum.name} - Enumeration Flowchart</h1>
        
        <div class="mermaid">
{mermaid_code}
        </div>
        
        {values_html}
        
        <h2>Mermaid Source Code</h2>
        <pre>
{mermaid_code}
        </pre>
        
        <p><small>Generated by Codesys XML Documentation Generator • Using Mermaid v10.6.1</small></p>
    </div>
</body>
</html>"""
        return html

    def _save_file(self, name: str, output_dir: Path, html: str, item_type: str) -> str:
        """Save HTML file and return path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.html"
        filepath = output_dir / filename

        self.logger.info(f"[FlowchartGenerator] Saving {item_type} to: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(filepath)