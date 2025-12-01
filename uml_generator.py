"""
Simple UML Generator - Shows ALL enum values
"""

import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class UMLGenerator:
    """Generates documentation showing ALL enum values"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_uml_for_union(self, union, xml_export, output_dir: Path) -> str:
        """Generate diagram for a union"""
        try:
            output_dir.mkdir(exist_ok=True)

            self.logger.info(f"Generating documentation for union: {union.name}")

            # Build enum lookup
            enum_lookup = {}
            if xml_export and hasattr(xml_export, 'enums'):
                for enum in xml_export.enums:
                    enum_lookup[enum.name.lower()] = enum
                    self.logger.info(f"Found enum: {enum.name} with {len(enum.values)} values")

            # Generate Mermaid erDiagram
            mermaid_code = self._create_simple_er_diagram(union, enum_lookup)

            # Create simple HTML
            html = self._create_simple_html_page(union, mermaid_code, enum_lookup)

            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{union.name}_{timestamp}.html"
            filepath = output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)

            self.logger.info(f"Created documentation: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Error: {str(e)}", exc_info=True)
            return ""

    def _create_simple_er_diagram(self, union, enum_lookup: Dict[str, Any]) -> str:
        """Create simple erDiagram showing all enum values"""
        lines = ["erDiagram"]

        # Union entity
        lines.append(f'    {union.name} {{')

        for member in union.members:
            if member.type.upper() in {'INT', 'BOOL', 'REAL', 'DINT', 'LINT', 'SINT', 'USINT',
                                      'UINT', 'UDINT', 'ULINT', 'BYTE', 'WORD', 'DWORD', 'LWORD'}:
                lines.append(f'    {member.type.upper()} {member.name}')
            else:
                lines.append(f'    enum {member.name}')

        lines.append('}')

        # Add all enum entities with ALL values
        for member in union.members:
            member_type_lower = member.type.lower()
            if member_type_lower in enum_lookup:
                enum = enum_lookup[member_type_lower]
                lines.append(f'    {member.type} {{')

                # Show ALL values - no truncation
                for value in enum.values:
                    lines.append(f'        int {value.name} "{value.value}"')

                lines.append('}')

                # Relationship
                lines.append(f'    {union.name} ||--|| {member.type} : "{member.name}"')

        return '\n'.join(lines)

    def _create_simple_html_page(self, union, mermaid_code: str, enum_lookup: Dict[str, Any]) -> str:
        """Create simple HTML page showing ALL values"""
        # Create enum tables with ALL values
        enum_tables = ""
        for member in union.members:
            member_type_lower = member.type.lower()
            if member_type_lower in enum_lookup:
                enum = enum_lookup[member_type_lower]
                enum_tables += self._create_complete_enum_table(member.type, enum, union.name, member.name)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{union.name} - Union Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            er: {{ useMaxWidth: false }}
        }});
    </script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4A90E2; padding-bottom: 10px; }}
        .mermaid {{ margin: 20px 0; background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; min-height: 500px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #4A90E2; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .union-info {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4A90E2; }}
        .enum-section {{ background: #f0f8e8; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #7CB342; }}
        pre {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{union.name} - Complete Union Documentation</h1>
        
        <div class="union-info">
            <h3>Union Information</h3>
            <p><strong>Type:</strong> Union</p>
            <p><strong>Members:</strong> {len(union.members)}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <h2>Entity Relationship Diagram</h2>
        <div class="mermaid">
{mermaid_code}
        </div>
        
        <div class="union-info">
            <h3>Union Members</h3>
            <ul>
"""

        # Add all union members
        for member in union.members:
            html += f"<li><strong>{member.name}</strong>: {member.type}</li>\n"

        html += """            </ul>
        </div>
        
        <h2>Complete Enumeration Values</h2>
"""

        if enum_tables:
            html += enum_tables
        else:
            html += '<div class="union-info"><p>No enumerations found in this union.</p></div>'

        html += f"""
        <h2>Mermaid Source Code</h2>
        <pre>
{mermaid_code}
        </pre>
        
        <p><small>Generated by Codesys XML Documentation Generator</small></p>
    </div>
    
    <script>
        // Simple debugging
        setTimeout(() => {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                console.log('Diagram rendered successfully');
                // Make diagram scrollable if too wide
                if (svg.clientWidth > 1000) {{
                    svg.style.minWidth = svg.clientWidth + 'px';
                }}
            }}
        }}, 1000);
    </script>
</body>
</html>"""

        return html

    def _create_complete_enum_table(self, enum_name: str, enum, union_name: str, member_name: str) -> str:
        """Create complete enum table with ALL values"""
        table = f"""
        <div class="enum-section">
            <h3>{enum_name} Enumeration ({len(enum.values)} values)</h3>
            <p><em>Used by: {union_name}.{member_name}</em></p>
            <table>
                <tr><th>Constant Name</th><th>Value</th><th>Description</th></tr>
        """

        # Add ALL values
        for value in enum.values:
            desc = getattr(value, 'description', '') or ''
            table += f"<tr><td>{value.name}</td><td>{value.value}</td><td>{desc}</td></tr>\n"

        table += """
            </table>
        </div>
        """
        return table