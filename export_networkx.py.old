"""
NetworkX export module for Codesys XML documentation
Generates graph-based documentation with recursive structure exploration
"""

import networkx as nx
import logging
from pathlib import Path
import json


class NetworkXExporter:
    """Exports Codesys XML data to NetworkX graphs for visualization and documentation"""

    def __init__(self, json_data):
        self.json_data = json_data
        self.logger = logging.getLogger('CodesysXMLDocGenerator.Exporter')
        self.graph = nx.DiGraph()
        self.exported_items = set()

    def export_item_structure(self, item_name, item_type=None):
        """
        Export the complete recursive structure of an item

        Args:
            item_name: Name of the item to export
            item_type: Type of item (dataType, pou, enum, union, structure, global_var)

        Returns:
            NetworkX graph representing the item's complete structure
        """
        self.logger.debug(f"Exporting structure for: {item_name} (type: {item_type})")
        self.graph = nx.DiGraph()
        self.exported_items = set()

        # Find the item in the JSON data
        item_data = self._find_item(item_name, item_type)
        if not item_data:
            self.logger.warning(f"Item not found: {item_name} (type: {item_type})")
            return self.graph

        # Add the root item and recursively explore its structure
        self._add_item_to_graph(item_data, is_root=True)

        self.logger.info(
            f"Exported structure for {item_name}: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
        return self.graph

    def _find_item(self, item_name, item_type=None):
        """Find an item in the JSON data by name and optionally type"""
        # Search in different sections based on type hint
        search_sections = []

        if item_type:
            # Search in specific section based on type
            type_to_section = {
                'dataType': 'DataTypes',
                'pou': 'POUs',
                'enum': 'Enums',
                'union': 'Unions',
                'structure': 'Structures',
                'global_var': 'GlobalVariables'
            }
            section = type_to_section.get(item_type)
            if section and section in self.json_data:
                search_sections.append((section, self.json_data[section]))
        else:
            # Search in all sections
            for section in ['DataTypes', 'POUs', 'Enums', 'Unions', 'Structures', 'GlobalVariables']:
                if section in self.json_data:
                    search_sections.append((section, self.json_data[section]))

        # Perform the search
        for section_name, section_data in search_sections:
            for item in section_data:
                if item.get('name') == item_name:
                    item['_section'] = section_name
                    item['_item_type'] = item_type or self._infer_item_type(item)
                    return item

        return None

    def _infer_item_type(self, item):
        """Infer the item type from its structure"""
        if 'pou_type' in item:
            return 'pou'
        elif item.get('type') in ['enum', 'union', 'structure', 'dataType']:
            return item['type']
        elif 'global_vars_group' in item:
            return 'global_var'
        return 'unknown'

    def _add_item_to_graph(self, item_data, parent_id=None, relationship=None, is_root=False):
        """Recursively add item and its dependencies to the graph"""
        item_name = item_data.get('name', 'Unknown')
        item_type = item_data.get('_item_type', 'unknown')
        item_section = item_data.get('_section', 'Unknown')

        # Create unique node ID
        node_id = f"{item_section}:{item_name}"

        # Avoid infinite recursion
        if node_id in self.exported_items:
            if parent_id:
                self.graph.add_edge(parent_id, node_id, relationship=relationship)
            return

        self.exported_items.add(node_id)

        # Add the node
        node_attributes = {
            'name': item_name,
            'type': item_type,
            'section': item_section,
            'details': self._extract_item_details(item_data),
            'is_root': is_root
        }
        self.graph.add_node(node_id, **node_attributes)

        # Add edge from parent if exists
        if parent_id:
            self.graph.add_edge(parent_id, node_id, relationship=relationship)

        # Recursively explore dependencies based on item type
        if item_type == 'pou':
            self._explore_pou_dependencies(item_data, node_id)
        elif item_type == 'structure':
            self._explore_structure_dependencies(item_data, node_id)
        elif item_type == 'union':
            self._explore_union_dependencies(item_data, node_id)
        elif item_type == 'enum':
            self._explore_enum_dependencies(item_data, node_id)
        elif item_type == 'dataType':
            self._explore_datatype_dependencies(item_data, node_id)
        elif item_type == 'global_var':
            self._explore_global_var_dependencies(item_data, node_id)

    def _extract_item_details(self, item_data):
        """Extract relevant details for the item"""
        details = {}

        if 'details' in item_data:
            details.update(item_data['details'])

        if 'pou_type' in item_data:
            details['pou_type'] = item_data['pou_type']

        if 'base_type' in item_data:
            details['base_type'] = item_data['base_type']

        if 'values' in item_data:
            details['values_count'] = len(item_data['values'])

        if 'members' in item_data:
            details['members_count'] = len(item_data['members'])

        return details

    def _explore_pou_dependencies(self, pou_data, node_id):
        """Explore dependencies of a POU"""
        details = pou_data.get('details', {})

        # Explore interface variables
        for var in details.get('variables', []):
            var_type = var.get('type', 'UNKNOWN')
            if var_type != 'UNKNOWN' and not self._is_basic_type(var_type):
                # Look for the type definition
                type_item = self._find_item(var_type)
                if type_item:
                    self._add_item_to_graph(type_item, node_id, f"variable_type:{var['name']}")

        # Explore actions and methods
        for action in pou_data.get('actions', []):
            self._explore_pou_dependencies(action, node_id)

        for method in pou_data.get('methods', []):
            self._explore_pou_dependencies(method, node_id)

    def _explore_structure_dependencies(self, struct_data, node_id):
        """Explore dependencies of a structure"""
        for member in struct_data.get('members', []):
            member_type = member.get('type', 'UNKNOWN')
            if member_type != 'UNKNOWN' and not self._is_basic_type(member_type):
                # Look for the type definition
                type_item = self._find_item(member_type)
                if type_item:
                    self._add_item_to_graph(type_item, node_id, f"member_type:{member['name']}")

    def _explore_union_dependencies(self, union_data, node_id):
        """Explore dependencies of a union"""
        for member in union_data.get('members', []):
            member_type = member.get('type', 'UNKNOWN')
            if member_type != 'UNKNOWN' and not self._is_basic_type(member_type):
                # Look for the type definition
                type_item = self._find_item(member_type)
                if type_item:
                    self._add_item_to_graph(type_item, node_id, f"member_type:{member['name']}")

    def _explore_enum_dependencies(self, enum_data, node_id):
        """Explore dependencies of an enum"""
        base_type = enum_data.get('base_type')
        if base_type and not self._is_basic_type(base_type):
            type_item = self._find_item(base_type)
            if type_item:
                self._add_item_to_graph(type_item, node_id, "base_type")

    def _explore_datatype_dependencies(self, datatype_data, node_id):
        """Explore dependencies of a data type"""
        details = datatype_data.get('details', {})
        base_type = details.get('base_type')
        if base_type and not self._is_basic_type(base_type):
            type_item = self._find_item(base_type)
            if type_item:
                self._add_item_to_graph(type_item, node_id, "base_type")

    def _explore_global_var_dependencies(self, global_var_data, node_id):
        """Explore dependencies of a global variable"""
        var_type = global_var_data.get('type', 'UNKNOWN')
        if var_type != 'UNKNOWN' and not self._is_basic_type(var_type):
            type_item = self._find_item(var_type)
            if type_item:
                self._add_item_to_graph(type_item, node_id, "variable_type")

    def _is_basic_type(self, type_name):
        """Check if a type is a basic/built-in type"""
        basic_types = {
            'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD',
            'SINT', 'USINT', 'INT', 'UINT', 'DINT', 'UDINT', 'LINT', 'ULINT',
            'REAL', 'LREAL', 'TIME', 'DATE', 'TIME_OF_DAY', 'DATE_AND_TIME',
            'STRING', 'WSTRING', 'UNKNOWN'
        }
        return type_name.upper() in basic_types

    def generate_documentation(self, graph, output_format='text'):
        """
        Generate documentation from the graph

        Args:
            graph: NetworkX graph to document
            output_format: 'text', 'html', or 'json'

        Returns:
            Documentation string in the requested format
        """
        if output_format == 'text':
            return self._generate_text_documentation(graph)
        elif output_format == 'html':
            return self._generate_html_documentation(graph)
        elif output_format == 'json':
            return self._generate_json_documentation(graph)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_text_documentation(self, graph):
        """Generate text documentation"""
        lines = []

        # Find root node
        root_nodes = [node for node, attrs in graph.nodes(data=True) if attrs.get('is_root', False)]
        if not root_nodes:
            if graph.nodes:
                root_nodes = [list(graph.nodes.keys())[0]]
            else:
                return "No data to document"

        root_node = root_nodes[0]
        root_attrs = graph.nodes[root_node]

        lines.append(f"=== COMPLETE STRUCTURE DOCUMENTATION ===")
        lines.append(f"Root Item: {root_attrs['name']} ({root_attrs['type']})")
        lines.append(f"Section: {root_attrs['section']}")
        lines.append("")

        # Add root details
        lines.append("ROOT ITEM DETAILS:")
        lines.extend(self._format_details(root_attrs['details'], indent=2))
        lines.append("")

        # Add dependencies
        lines.append("DEPENDENCY TREE:")
        self._add_dependency_tree_text(graph, root_node, lines, indent=0)

        return '\n'.join(lines)

    def _add_dependency_tree_text(self, graph, current_node, lines, indent=0):
        """Recursively add dependency tree to text documentation"""
        indent_str = "  " * indent
        attrs = graph.nodes[current_node]

        # Skip if this is the root (already documented)
        if indent > 0:
            lines.append(f"{indent_str}└── {attrs['name']} ({attrs['type']})")

            # Add details for this node
            if attrs['details']:
                detail_lines = self._format_details(attrs['details'], indent + 3)
                lines.extend([f"{indent_str}     {line}" for line in detail_lines])

        # Recursively process children
        for successor in graph.successors(current_node):
            edge_data = graph.edges[current_node, successor]
            relationship = edge_data.get('relationship', 'depends_on')

            if indent == 0:
                lines.append(f"  └── {relationship}:")

            self._add_dependency_tree_text(graph, successor, lines, indent + 2)

    def _format_details(self, details, indent=0):
        """Format details dictionary as text lines"""
        lines = []
        indent_str = " " * indent

        for key, value in details.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.extend(self._format_details(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.extend(self._format_details(item, indent + 2))
                    else:
                        lines.append(f"{indent_str}  - {item}")
            else:
                lines.append(f"{indent_str}{key}: {value}")

        return lines

    def _generate_html_documentation(self, graph):
        """Generate HTML documentation (simplified version)"""
        text_doc = self._generate_text_documentation(graph)
        html_doc = f"""
        <html>
        <head>
            <title>Codesys Structure Documentation</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .root-item {{ color: #2c3e50; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Codesys Structure Documentation</h1>
            <pre>{text_doc}</pre>
        </body>
        </html>
        """
        return html_doc

    def _generate_json_documentation(self, graph):
        """Generate JSON documentation"""
        documentation = {
            'graph_structure': nx.node_link_data(graph),
            'summary': {
                'nodes': len(graph.nodes),
                'edges': len(graph.edges),
                'root_nodes': [node for node, attrs in graph.nodes(data=True) if attrs.get('is_root', False)]
            }
        }
        return json.dumps(documentation, indent=2, ensure_ascii=False)

    def export_to_file(self, graph, filename, output_format='text'):
        """Export documentation to file"""
        documentation = self.generate_documentation(graph, output_format)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(documentation)

        self.logger.info(f"Documentation exported to: {filename}")
        return filename