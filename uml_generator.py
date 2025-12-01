"""
Simple UML Generator - Shows ALL values (Mermaid erDiagram format)
"""

import logging
import traceback
from typing import Dict, Any, List, Set, Tuple
from pathlib import Path
from datetime import datetime


class UMLGenerator:
    """Generates documentation showing ALL values using Mermaid erDiagram"""

    # Class variable to track instances
    _instance_count = 0

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        UMLGenerator._instance_count += 1
        self.instance_id = UMLGenerator._instance_count
        self.logger.info(f"[UMLGenerator_{self.instance_id}] Initialized - Mermaid erDiagram version")

    def generate_uml_for_structure(self, structure, xml_export, output_dir: Path) -> str:
        """Generate Mermaid erDiagram for a structure with all nested types"""
        try:
            self.logger.info(f"[UMLGenerator_{self.instance_id}] ===== START generate_uml_for_structure =====")
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Structure: {structure.name}")

            # Build complete type lookup
            type_lookup = self._build_type_lookup(xml_export)

            # Find all related types (recursive)
            all_types = self._find_all_related_types(structure, type_lookup)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Found {len(all_types)} related types for structure {structure.name}")

            # Generate Mermaid erDiagram
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Generating Mermaid erDiagram...")
            mermaid_code = self._create_structure_diagram(structure, all_types, type_lookup)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Mermaid code generated: {len(mermaid_code)} chars")

            # Create HTML page
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Creating HTML page...")
            html = self._create_structure_html_page(structure, mermaid_code, all_types, type_lookup)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] HTML generated: {len(html)} chars")

            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{structure.name}_{timestamp}.html"
            filepath = output_dir / filename

            self._save_html_file(filepath, html, "Structure")

            self.logger.info(f"[UMLGenerator_{self.instance_id}] ===== END generate_uml_for_structure =====")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"[UMLGenerator_{self.instance_id}] Error generating UML: {str(e)}", exc_info=True)
            self.logger.error(f"[UMLGenerator_{self.instance_id}] Full traceback:\n{traceback.format_exc()}")
            return ""

    def generate_uml_for_union(self, union, xml_export, output_dir: Path) -> str:
        """Generate Mermaid erDiagram for a union"""
        try:
            self.logger.info(f"[UMLGenerator_{self.instance_id}] ===== START generate_uml_for_union =====")
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Union: {union.name}")

            # Build complete type lookup
            type_lookup = self._build_type_lookup(xml_export)

            # Generate Mermaid erDiagram
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Generating Mermaid erDiagram...")
            mermaid_code = self._create_union_diagram(union, type_lookup)
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Mermaid code generated: {len(mermaid_code)} chars")

            # Create HTML page
            self.logger.info(f"[UMLGenerator_{self.instance_id}] Creating HTML page...")
            html = self._create_union_html_page(union, mermaid_code, type_lookup)
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

            # Add data types
            if hasattr(xml_export, 'data_types'):
                for data_type in xml_export.data_types:
                    type_lookup[data_type.name] = ('datatype', data_type)
                    type_lookup[data_type.name.lower()] = ('datatype', data_type)

            self.logger.info(f"[UMLGenerator_{self.instance_id}] Built type lookup with {len(type_lookup)//2} unique types")

        return type_lookup

    def _find_all_related_types(self, start_type, type_lookup, visited=None):
        """Recursively find all related types (structures, unions, enums)"""
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
                    # Get the actual type object
                    type_key = member_type if member_type in type_lookup else member_type_lower
                    type_info = type_lookup.get(type_key)

                    if type_info:
                        type_obj = type_info[1]
                        # Recursively find related types for this type
                        self._find_all_related_types(type_obj, type_lookup, visited)

        return visited

    def _is_basic_type(self, type_name):
        """Check if a type is a basic type"""
        type_upper = type_name.upper()
        return type_upper in {'INT', 'BOOL', 'REAL', 'DINT', 'LINT', 'SINT', 'USINT',
                             'UINT', 'UDINT', 'ULINT', 'BYTE', 'WORD', 'DWORD', 'LWORD',
                             'STRING', 'CHAR', 'WCHAR', 'TIME', 'DATE', 'DT', 'TOD'}

    def _create_structure_diagram(self, structure, all_types, type_lookup):
        """Create Mermaid erDiagram for a structure with all related types"""
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] [_create_structure_diagram] Creating erDiagram for structure: {structure.name}")

        lines = ["erDiagram"]
        lines.append("")

        # First, add all structures/unions as entities
        for type_name in all_types:
            type_info = type_lookup.get(type_name) or type_lookup.get(type_name.lower())
            if type_info:
                type_category, type_obj = type_info

                if type_category in ['structure', 'union']:
                    lines.append(f"    {type_name} {{")

                    for member in type_obj.members:
                        member_type = member.type.upper() if self._is_basic_type(member.type) else member.type

                        # Check if member type is another structure/union/enum
                        if member.type in all_types or member.type.lower() in all_types:
                            # It's a related type, mark it as such
                            lines.append(f"        ref {member.name}")
                        elif self._is_basic_type(member.type):
                            lines.append(f"        {member_type} {member.name}")
                        else:
                            # Check if it's an enum
                            member_type_info = type_lookup.get(member.type) or type_lookup.get(member.type.lower())
                            if member_type_info and member_type_info[0] == 'enum':
                                lines.append(f"        enum {member.name}")
                            else:
                                lines.append(f"        {member_type} {member.name}")

                    lines.append("    }")
                    lines.append("")

        # Then, add all enums as entities
        for type_name in all_types:
            type_info = type_lookup.get(type_name) or type_lookup.get(type_name.lower())
            if type_info:
                type_category, type_obj = type_info

                if type_category == 'enum':
                    lines.append(f"    {type_name} {{")

                    # Show ALL values
                    for value in type_obj.values:
                        lines.append(f"        int {value.name} \"{value.value}\"")

                    lines.append("    }")
                    lines.append("")

        # Finally, add relationships
        for type_name in all_types:
            type_info = type_lookup.get(type_name) or type_lookup.get(type_name.lower())
            if type_info:
                type_category, type_obj = type_info

                if type_category in ['structure', 'union']:
                    for member in type_obj.members:
                        member_type = member.type
                        member_type_lower = member.type.lower()

                        # Check if member type is another structure/union/enum in our diagram
                        if member_type in all_types or member_type_lower in all_types:
                            # Determine relationship type
                            target_type = member_type if member_type in all_types else member_type_lower
                            target_info = type_lookup.get(target_type)

                            if target_info:
                                target_category, _ = target_info

                                # Structure/Union contains another Structure/Union (composition)
                                if target_category in ['structure', 'union']:
                                    lines.append(f'    {type_name} ||--|| {member_type} : "{member.name}"')
                                # Structure/Union references an Enum
                                elif target_category == 'enum':
                                    lines.append(f'    {type_name} ||--|| {member_type} : "{member.name}"')

        # Remove duplicate relationships
        unique_lines = []
        seen_relationships = set()
        for line in lines:
            if '||--||' in line:
                if line not in seen_relationships:
                    unique_lines.append(line)
                    seen_relationships.add(line)
            else:
                unique_lines.append(line)

        result = '\n'.join(unique_lines)
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] Structure diagram code:\n{result}")

        return result

    def _create_union_diagram(self, union, type_lookup):
        """Create Mermaid erDiagram for a union"""
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] [_create_union_diagram] Creating erDiagram for union: {union.name}")

        lines = ["erDiagram"]
        lines.append("")

        # Union entity
        lines.append(f"    {union.name} {{")

        for member in union.members:
            member_type = member.type.upper() if self._is_basic_type(member.type) else member.type

            # Check if member type is an enum
            member_type_lower = member.type.lower()
            if member_type_lower in type_lookup:
                type_info = type_lookup[member_type_lower]
                if type_info[0] == 'enum':
                    lines.append(f"        enum {member.name}")
                else:
                    lines.append(f"        {member_type} {member.name}")
            else:
                lines.append(f"        {member_type} {member.name}")
        lines.append("    }")
        lines.append("")

        # Add enum entities and relationships
        for member in union.members:
            member_type_lower = member.type.lower()
            if member_type_lower in type_lookup:
                type_info = type_lookup[member_type_lower]
                if type_info[0] == 'enum':
                    enum = type_info[1]

                    lines.append(f"    {member.type} {{")

                    # Show ALL values
                    for value in enum.values:
                        lines.append(f"        int {value.name} \"{value.value}\"")

                    lines.append("    }")
                    lines.append("")

                    # Relationship (one-to-one relationship between union and enum)
                    lines.append(f'    {union.name} ||--|| {member.type} : "{member.name}"')

        result = '\n'.join(lines)
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] Union diagram code:\n{result}")

        return result

    def _create_single_enum_diagram(self, enum) -> str:
        """Create Mermaid erDiagram for a single enum"""
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] [_create_single_enum_diagram] Creating erDiagram for enum: {enum.name}")

        lines = ["erDiagram"]
        lines.append("")

        # Single enum entity
        lines.append(f"    {enum.name} {{")

        # Show ALL values
        for value in enum.values:
            lines.append(f"        int {value.name} \"{value.value}\"")

        lines.append("    }")

        result = '\n'.join(lines)
        self.logger.debug(f"[UMLGenerator_{self.instance_id}] Single enum erDiagram code:\n{result}")

        return result

    def _create_structure_html_page(self, structure, mermaid_code: str, all_types, type_lookup):
        """Create HTML page for structure diagram"""
        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{structure.name} - Structure Documentation</title>
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
        .mermaid {{ margin: 20px 0; background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; min-height: 500px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #4A90E2; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .type-info {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4A90E2; }}
        .enum-info {{ background: #f0f8e8; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #7CB342; }}
        pre {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 14px; white-space: pre-wrap; word-wrap: break-word; }}
        .mermaid svg {{ min-width: 100%; }}
        .note {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .type-list {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{structure.name} - Complete Structure Documentation</h1>
        
        <div class="type-info">
            <h3>Structure Information</h3>
            <p><strong>Type:</strong> Structure</p>
            <p><strong>Members:</strong> {len(structure.members)}</p>
            <p><strong>Related Types:</strong> {len(all_types)} total types in diagram</p>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="type-list">
            <h4>Types included in this diagram:</h4>
            <ul>
"""

        # List all types in the diagram
        for type_name in sorted(all_types):
            type_info = type_lookup.get(type_name) or type_lookup.get(type_name.lower())
            if type_info:
                type_category, type_obj = type_info
                html += f"<li><strong>{type_name}</strong> ({type_category})</li>\n"

        html += """            </ul>
        </div>
        
        <h2>Entity Relationship Diagram</h2>
        <div class="note">
            <strong>Note:</strong> This diagram shows the complete structure hierarchy with all nested types.
            Relationships show composition (||--||) between types.
        </div>
        <div class="mermaid">
{mermaid_code}
        </div>
        
        <h2>Type Details</h2>
"""

        # Add details for each type
        for type_name in sorted(all_types):
            type_info = type_lookup.get(type_name) or type_lookup.get(type_name.lower())
            if type_info:
                type_category, type_obj = type_info

                if type_category in ['structure', 'union']:
                    html += f"""
        <div class="type-info">
            <h3>{type_name} ({'Union' if type_category == 'union' else 'Structure'})</h3>
            <table>
                <thead>
                    <tr><th>Member</th><th>Type</th><th>Description</th></tr>
                </thead>
                <tbody>
"""
                    for member in type_obj.members:
                        desc = getattr(member, 'description', '') or ''
                        html += f"<tr><td>{member.name}</td><td>{member.type}</td><td>{desc}</td></tr>\n"

                    html += """                </tbody>
            </table>
        </div>
"""
                elif type_category == 'enum':
                    html += f"""
        <div class="enum-info">
            <h3>{type_name} Enumeration ({len(type_obj.values)} values)</h3>
            <table>
                <thead>
                    <tr><th>#</th><th>Constant Name</th><th>Value</th><th>Description</th></tr>
                </thead>
                <tbody>
"""
                    for i, value in enumerate(type_obj.values, 1):
                        desc = getattr(value, 'description', '') or ''
                        html += f"<tr><td>{i}</td><td>{value.name}</td><td>{value.value}</td><td>{desc}</td></tr>\n"

                    html += """                </tbody>
            </table>
        </div>
"""

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

    def _create_union_html_page(self, union, mermaid_code: str, type_lookup):
        """Create HTML page for union diagram"""
        # Create enum tables
        enum_tables = ""
        for member in union.members:
            member_type_lower = member.type.lower()
            if member_type_lower in type_lookup:
                type_info = type_lookup[member_type_lower]
                if type_info[0] == 'enum':
                    enum = type_info[1]
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
            member_type = member.type.upper() if self._is_basic_type(member.type) else member.type
            member_type_lower = member.type.lower()

            if self._is_basic_type(member.type):
                html += f"<li><strong>{member.name}</strong>: {member_type} (basic type)</li>\n"
            elif member_type_lower in type_lookup:
                type_info = type_lookup[member_type_lower]
                if type_info[0] == 'enum':
                    html += f"<li><strong>{member.name}</strong>: {member.type} (enumeration - see table below)</li>\n"
                else:
                    html += f"<li><strong>{member.name}</strong>: {member.type}</li>\n"
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