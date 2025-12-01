"""
Simple UML Generator - Shows ALL enum values (Mermaid erDiagram format)
"""

import logging
import traceback
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class UMLGenerator:
    """Generates documentation showing ALL enum values using Mermaid erDiagram"""

    # Class variable to track instances
    _instance_count = 0

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        UMLGenerator._instance_count += 1
        self.instance_id = UMLGenerator._instance_count
        self.logger.info(f"[UMLGenerator_{self.instance_id}] Initialized - Mermaid erDiagram version")

    def generate_uml_for_union(self, union, xml_export, output_dir: Path) -> str:
        """Generate Mermaid erDiagram for a union"""
        try:
            self.logger.info(f"[UMLGenerator_{self.instance_id}] ===== START generate_uml_for_union =====")
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Union: {union.name}")

            # Build enum lookup - Get ALL enums
            enum_lookup = self._build_enum_lookup(xml_export, union)

            # Generate Mermaid erDiagram
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Generating Mermaid erDiagram...")
            mermaid_code = self._create_mermaid_er_diagram(union, enum_lookup)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Mermaid code generated: {len(mermaid_code)} chars")

            # Create HTML page
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Creating HTML page...")
            html = self._create_union_html_page(union, mermaid_code, enum_lookup)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] HTML generated: {len(html)} chars")

            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{union.name}_{timestamp}.html"
            filepath = output_dir / filename

            self._save_html_file(filepath, html, "Union")

            self.logger.info(f"[UMLGenerator_{self.instance_id}] ===== END generate_uml_for_union =====")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"[UMLGenerator_{self.instance_id}] Error generating UML: {str(e)}", exc_info=True)
            self.logger.error(f"[UMLGenerator_{self.instance_id}] Full traceback:\n{traceback.format_exc()}")
            return ""

    def generate_uml_for_enum(self, enum, output_dir: Path) -> str:
        """Generate Mermaid erDiagram for a single enum"""
        try:
            self.logger.info(f"[UMLGenerator_{self.instance_id}] ===== START generate_uml_for_enum =====")
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Enum: {enum.name} with {len(enum.values)} values")

            # Generate Mermaid erDiagram for single enum
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Generating Mermaid erDiagram...")
            mermaid_code = self._create_single_enum_diagram(enum)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Mermaid code generated: {len(mermaid_code)} chars")

            # Create HTML page
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Creating HTML page...")
            html = self._create_enum_html_page(enum, mermaid_code)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] HTML generated: {len(html)} chars")

            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{enum.name}_{timestamp}.html"
            filepath = output_dir / filename

            self._save_html_file(filepath, html, "Enum")

            self.logger.info(f"[UMLGenerator_{self.instance_id}] ===== END generate_uml_for_enum =====")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"[UMLGenerator_{self.instance_id}] Error generating UML: {str(e)}", exc_info=True)
            self.logger.error(f"[UMLGenerator_{self.instance_id}] Full traceback:\n{traceback.format_exc()}")
            return ""

    def _build_enum_lookup(self, xml_export, union=None):
        """Build enum lookup from XML export"""
        enum_lookup = {}
        if xml_export and hasattr(xml_export, 'enums'):
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Found {len(xml_export.enums)} total enums in XML")

            # Get ALL enums
            for i, enum in enumerate(xml_export.enums):
                # Store with multiple keys for easier lookup
                enum_lookup[enum.name] = enum
                enum_lookup[enum.name.lower()] = enum

                # Only log first 10 for debugging
                if i < 10:
                    self.logger.debug(f"[UMLGenerator_{self.instance_id}] Enum [{i}]: {enum.name} ({len(enum.values)} values)")

            if len(xml_export.enums) > 10:
                self.logger.debug(f"[UMLGenerator_{self.instance_id}] ... and {len(xml_export.enums) - 10} more enums")

            # Log specific lookup for debugging if union provided
            if union:
                self.logger.debug(f"[UMLGenerator_{self.instance_id}] Total enum lookup entries: {len(enum_lookup)//2} enums")

                # Check if the specific enums we need are in the lookup
                for member in union.members:
                    member_type_lower = member.type.lower()
                    if member_type_lower not in {'int', 'bool', 'real', 'dint', 'lint', 'sint', 'usint',
                                                'uint', 'udint', 'ulint', 'byte', 'word', 'dword', 'lword'}:
                        self.logger.debug(f"[UMLGenerator_{self.instance_id}] Checking for enum '{member.type}' in lookup...")
                        self.logger.debug(f"[UMLGenerator_{self.instance_id}]   Exact match: {member.type in enum_lookup}")
                        self.logger.debug(f"[UMLGenerator_{self.instance_id}]   Lowercase match: {member_type_lower in enum_lookup}")
        else:
            self.logger.warning(f"[UMLGenerator_{self.instance_id}] No enums found or xml_export is None")

        return enum_lookup

    def _create_mermaid_er_diagram(self, union, enum_lookup: Dict[str, Any]) -> str:
        """Create Mermaid erDiagram showing all enum values"""
        self.logger.debug(
            f"[UMLGenerator_{self.instance_id}] [_create_mermaid_er_diagram] Creating erDiagram for union: {union.name}")
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] Looking for enums in union members...")

        lines = ["erDiagram"]
        lines.append("")

        # Union entity - NO COMMENTS!
        lines.append(f"    {union.name} {{")

        for member in union.members:
            member_type = member.type.upper()
            # Check if it's a basic type
            if member_type in {'INT', 'BOOL', 'REAL', 'DINT', 'LINT', 'SINT', 'USINT',
                               'UINT', 'UDINT', 'ULINT', 'BYTE', 'WORD', 'DWORD', 'LWORD'}:
                lines.append(f"        {member_type} {member.name}")
                self.logger.debug(f"[UMLGenerator_{self.instance_id}] Basic type member: {member.name} : {member_type}")
            else:
                # Check if it's an enum (case-insensitive)
                member_type_lower = member.type.lower()
                self.logger.debug(
                    f"[UMLGenerator_{self.instance_id}] Checking if {member.type} (lower: {member_type_lower}) is in enum lookup...")

                # Try exact match first
                if member.type in enum_lookup:
                    lines.append(f"        enum {member.name}")
                    self.logger.debug(
                        f"[UMLGenerator_{self.instance_id}] Found exact match: {member.type} -> enum {member.name}")
                # Try case-insensitive match
                elif member_type_lower in enum_lookup:
                    lines.append(f"        enum {member.name}")
                    self.logger.debug(
                        f"[UMLGenerator_{self.instance_id}] Found case-insensitive match: {member_type_lower} -> enum {member.name}")
                else:
                    lines.append(f"        {member.type} {member.name}")
                    self.logger.debug(f"[UMLGenerator_{self.instance_id}] Not found in enum lookup: {member.type}")
        lines.append("    }")
        lines.append("")

        # Add all enum entities with ALL values - NO COMMENTS!
        enum_entities_added = []
        for member in union.members:
            member_type = member.type
            member_type_lower = member.type.lower()

            # Try multiple ways to find the enum
            enum_found = None
            if member_type in enum_lookup:
                enum_found = enum_lookup[member_type]
            elif member_type_lower in enum_lookup:
                enum_found = enum_lookup[member_type_lower]

            if enum_found and member.type not in enum_entities_added:
                enum_entities_added.append(member.type)
                self.logger.debug(
                    f"[UMLGenerator_{self.instance_id}] Adding enum entity: {member.type} with {len(enum_found.values)} values")

                lines.append(f"    {member.type} {{")

                # Show ALL values - no truncation, no comments
                for value in enum_found.values:
                    lines.append(f"        int {value.name} \"{value.value}\"")

                lines.append("    }")
                lines.append("")

                # Relationship (one-to-one relationship between union and enum)
                lines.append(f'    {union.name} ||--|| {member.type} : "{member.name}"')
                self.logger.debug(
                    f"[UMLGenerator_{self.instance_id}] Added relationship: {union.name} ||--|| {member.type} : \"{member.name}\"")

        result = '\n'.join(lines)
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] Mermaid erDiagram code:\n{result}")

        # Log summary
        self.logger.info(
            f"[UMLGenerator_{self.instance_id}] Created erDiagram with {len(enum_entities_added)} enum entities")

        return result



    def _create_union_html_page(self, union, mermaid_code: str, enum_lookup: Dict[str, Any]) -> str:
        """Create HTML page for union diagram"""
        # Create enum tables with ALL values
        enum_tables = ""
        for member in union.members:
            member_type_lower = member.type.lower()
            if member_type_lower in enum_lookup or member.type in enum_lookup:
                enum = enum_lookup.get(member_type_lower) or enum_lookup.get(member.type)
                if enum:
                    enum_tables += self._create_complete_enum_table(member.type, enum, union.name, member.name)

        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{union.name} - Union Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        // Configure Mermaid for erDiagram support
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            er: {{
                useMaxWidth: false,
                diagramPadding: 20
            }}
        }});
        
        // Simple render function
        function renderMermaid() {{
            console.log('Rendering Mermaid erDiagram...');
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }}
        
        // Render when page loads
        document.addEventListener('DOMContentLoaded', renderMermaid);
        setTimeout(renderMermaid, 100);
    </script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4A90E2; padding-bottom: 10px; }}
        .mermaid {{ margin: 20px 0; background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; min-height: 400px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #4A90E2; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .union-info {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4A90E2; }}
        .enum-info {{ background: #f0f8e8; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #7CB342; }}
        pre {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 14px; white-space: pre-wrap; word-wrap: break-word; }}
        .mermaid svg {{ min-width: 100%; }}
        .note {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{union.name} - Union Documentation</h1>
        
        <div class="union-info">
            <h3>Union Information</h3>
            <p><strong>Type:</strong> Union</p>
            <p><strong>Members:</strong> {len(union.members)}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <h2>Entity Relationship Diagram</h2>
        <div class="note">
            <strong>Note:</strong> This diagram shows the union structure and its relationship to enumerations.
        </div>
        <div class="mermaid">
{mermaid_code}
        </div>
        
        <div class="union-info">
            <h3>Union Members</h3>
            <ul>
"""

        # Add all union members with type info
        for member in union.members:
            member_type = member.type.upper()
            if member_type in {'INT', 'BOOL', 'REAL', 'DINT', 'LINT', 'SINT', 'USINT',
                              'UINT', 'UDINT', 'ULINT', 'BYTE', 'WORD', 'DWORD', 'LWORD'}:
                html += f"<li><strong>{member.name}</strong>: {member_type} (basic type)</li>\n"
            elif member.type.lower() in enum_lookup or member.type in enum_lookup:
                html += f"<li><strong>{member.name}</strong>: {member.type} (enumeration - see table below)</li>\n"
            else:
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
        
        <p><small>Generated by Codesys XML Documentation Generator • Using Mermaid v10.6.1</small></p>
    </div>
</body>
</html>"""

        return html

    def _create_enum_html_page(self, enum, mermaid_code: str) -> str:
        """Create HTML page for single enum diagram"""
        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{enum.name} - Enumeration Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        // Configure Mermaid for erDiagram support
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            er: {{
                useMaxWidth: false,
                diagramPadding: 20
            }}
        }});
        
        // Simple render function
        function renderMermaid() {{
            console.log('Rendering Mermaid erDiagram...');
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }}
        
        // Render when page loads
        document.addEventListener('DOMContentLoaded', renderMermaid);
        setTimeout(renderMermaid, 100);
    </script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4A90E2; padding-bottom: 10px; }}
        .mermaid {{ margin: 20px 0; background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; min-height: 300px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #4A90E2; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .enum-info {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4A90E2; }}
        pre {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 14px; white-space: pre-wrap; word-wrap: break-word; }}
        .mermaid svg {{ min-width: 100%; }}
        .note {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{enum.name} - Enumeration Documentation</h1>
        
        <div class="enum-info">
            <h3>Enumeration Information</h3>
            <p><strong>Type:</strong> Enumeration</p>
            <p><strong>Values:</strong> {len(enum.values)}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <h2>Entity Relationship Diagram</h2>
        <div class="note">
            <strong>Note:</strong> This diagram shows the enumeration structure with all its values.
        </div>
        <div class="mermaid">
{mermaid_code}
        </div>
        
        <div class="enum-info">
            <h3>Complete Enumeration Values</h3>
            <table>
                <thead>
                    <tr><th>#</th><th>Constant Name</th><th>Value</th><th>Description</th></tr>
                </thead>
                <tbody>
"""

        # Add ALL values with index
        for i, value in enumerate(enum.values, 1):
            desc = getattr(value, 'description', '') or ''
            html += f"<tr><td>{i}</td><td>{value.name}</td><td>{value.value}</td><td>{desc}</td></tr>\n"

        html += f"""
                </tbody>
            </table>
        </div>
        
        <h2>Mermaid Source Code</h2>
        <pre>
{mermaid_code}
        </pre>
        
        <p><small>Generated by Codesys XML Documentation Generator • Using Mermaid v10.6.1</small></p>
    </div>
</body>
</html>"""

        return html

    def _save_html_file(self, filepath: Path, html: str, item_type: str):
        """Save HTML file and verify"""
        self.logger.info(f"[UMLGenerator_{self.instance_id}] Saving {item_type} to: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        # Verify file was written
        if filepath.exists():
            file_size = filepath.stat().st_size
            self.logger.info(f"[UMLGenerator_{self.instance_id}] File saved successfully: {file_size} bytes")

            # Read back first few lines to verify content
            with open(filepath, 'r', encoding='utf-8') as f:
                first_lines = ''.join([next(f) for _ in range(5)])

            if "mermaid" in first_lines.lower():
                self.logger.info(f"[UMLGenerator_{self.instance_id}] [OK] File contains Mermaid - CORRECT")
            else:
                self.logger.warning(f"[UMLGenerator_{self.instance_id}] [WARN] File doesn't contain Mermaid keyword")
        else:
            self.logger.error(f"[UMLGenerator_{self.instance_id}] File was not created!")

    def _create_complete_enum_table(self, enum_name: str, enum, union_name: str, member_name: str) -> str:
        """Create complete enum table with ALL values"""
        table = f"""
        <div class="enum-info">
            <h3>{enum_name} Enumeration ({len(enum.values)} values)</h3>
            <p><em>Used by: {union_name}.{member_name}</em></p>
            <table>
                <thead>
                    <tr><th>#</th><th>Constant Name</th><th>Value</th><th>Description</th></tr>
                </thead>
                <tbody>
        """

        # Add ALL values with index
        for i, value in enumerate(enum.values, 1):
            desc = getattr(value, 'description', '') or ''
            table += f"<tr><td>{i}</td><td>{value.name}</td><td>{value.value}</td><td>{desc}</td></tr>\n"

        table += """
                </tbody>
            </table>
        </div>
        """
        return table

    def _create_single_enum_diagram(self, enum) -> str:
        """Create Mermaid erDiagram for a single enum"""
        self.logger.debug(
            f"[UMLGenerator_{self.instance_id}] [_create_single_enum_diagram] Creating erDiagram for enum: {enum.name}")

        lines = ["erDiagram"]
        lines.append("")

        # Single enum entity - NO COMMENTS INSIDE!
        lines.append(f"    {enum.name} {{")

        # Show ALL values - no truncation, no comments
        for value in enum.values:
            lines.append(f"        int {value.name} \"{value.value}\"")

        lines.append("    }")

        result = '\n'.join(lines)
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] Single enum erDiagram code:\n{result}")

        return result