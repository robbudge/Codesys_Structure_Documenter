"""
Details Manager for Codesys XML Parser GUI
Handles display of item details and export functionality
"""

import tkinter as tk
from tkinter import ttk, filedialog
import logging


class DetailsManager:
    """Manages the details display panel with export functionality"""

    def __init__(self, details_text, logger=None):
        self.details_text = details_text
        self.json_data = None
        self.logger = logger or logging.getLogger('CodesysXMLDocGenerator.GUI.DetailsManager')
        self.logger.debug("DetailsManager initialized")

    def set_json_data(self, json_data):
        """Set the JSON data for reference"""
        self.json_data = json_data
        self.logger.debug("JSON data set in DetailsManager")

    def clear_details(self):
        """Clear the details text widget"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.config(state=tk.DISABLED)
        self.logger.debug("Details cleared")

    def show_item_details(self, selected_item, tree):
        """Show details for the selected item"""
        self.clear_details()
        self.details_text.config(state=tk.NORMAL)

        try:
            item_text = selected_item['text']
            item_tags = selected_item['tags']
            item_id = selected_item['id']

            self.logger.debug(f"Showing details for: {item_text} with tags: {item_tags}")

            if 'category' in item_tags:
                self._show_category_details(item_text, tree, item_id)
            elif 'datatype' in item_tags:
                self._show_datatype_details(item_text)
            elif 'pou' in item_tags:
                self._show_pou_details(item_text)
            elif 'globalvar' in item_tags:
                self._show_global_var_details(item_text)
            elif 'enum' in item_tags:
                self._show_enum_details(item_text)
            elif 'union' in item_tags:
                self._show_union_details(item_text)
            elif 'structure' in item_tags:
                self._show_structure_details(item_text)
            elif 'structmember' in item_tags:
                self._show_structure_member_details(item_text, tree, item_id)
            elif 'enumvalue' in item_tags:
                self._show_enum_value_details(item_text, tree, item_id)
            elif 'unionmember' in item_tags:
                self._show_union_member_details(item_text, tree, item_id)
            elif 'action' in item_tags:
                self._show_action_details(item_text, tree, item_id)
            elif 'method' in item_tags:
                self._show_method_details(item_text, tree, item_id)
            elif 'pouvariable' in item_tags:
                self._show_pou_variable_details(item_text, tree, item_id)
            else:
                self.details_text.insert(tk.END, f"Unknown item type: {item_text}\nTags: {item_tags}")

        except Exception as e:
            self.logger.error(f"Error showing item details: {str(e)}", exc_info=True)
            self.details_text.insert(tk.END, f"Error displaying details: {str(e)}")

        finally:
            self.details_text.config(state=tk.DISABLED)

    def _show_category_details(self, category_name, tree, item_id):
        """Show details for a category"""
        self.details_text.insert(tk.END, f"Category: {category_name}\n")
        self.details_text.insert(tk.END, "=" * 50 + "\n\n")

        # Count items in this category
        children = tree.get_children(item_id)
        self.details_text.insert(tk.END, f"Items in category: {len(children)}\n")

        # Show first few items as examples
        if children:
            self.details_text.insert(tk.END, "\nSample items:\n")
            for i, child_id in enumerate(children[:5]):  # Show first 5 items
                child_text = tree.item(child_id, 'text')
                self.details_text.insert(tk.END, f"  - {child_text}\n")
            if len(children) > 5:
                self.details_text.insert(tk.END, f"  ... and {len(children) - 5} more items\n")

    def _show_datatype_details(self, datatype_name):
        """Show details for a Data Type"""
        datatype = self._find_datatype_by_name(datatype_name)
        if not datatype:
            self.details_text.insert(tk.END, f"Data Type '{datatype_name}' not found")
            return

        self.details_text.insert(tk.END, f"Data Type: {datatype_name}\n")
        self.details_text.insert(tk.END, "=" * 50 + "\n\n")

        details = datatype.get('details', {})
        if details:
            self.details_text.insert(tk.END, "Details:\n")
            for key, value in details.items():
                self.details_text.insert(tk.END, f"  {key}: {value}\n")

        # Add export button
        self._add_export_section(datatype)

    def _show_pou_details(self, pou_name):
        """Show details for a POU"""
        pou = self._find_pou_by_name(pou_name)
        if not pou:
            self.details_text.insert(tk.END, f"POU '{pou_name}' not found")
            return

        self.details_text.insert(tk.END, f"POU: {pou_name}\n")
        self.details_text.insert(tk.END, f"Type: {pou.get('pou_type', 'Unknown')}\n")
        self.details_text.insert(tk.END, "=" * 50 + "\n\n")

        details = pou.get('details', {})
        if details.get('variables'):
            self.details_text.insert(tk.END, f"Interface Variables: {len(details['variables'])}\n")
        if details.get('implementation'):
            self.details_text.insert(tk.END, "Has implementation code\n")
        if details.get('description'):
            self.details_text.insert(tk.END, f"Description: {details['description']}\n")

        # Add export button
        self._add_export_section(pou)

    def _show_global_var_details(self, var_name):
        """Show details for a Global Variable"""
        global_var = self._find_global_var_by_name(var_name)
        if not global_var:
            self.details_text.insert(tk.END, f"Global Variable '{var_name}' not found")
            return

        self.details_text.insert(tk.END, f"Global Variable: {var_name}\n")
        self.details_text.insert(tk.END, f"Group: {global_var.get('global_vars_group', 'Unknown')}\n")
        self.details_text.insert(tk.END, "=" * 50 + "\n\n")

        self.details_text.insert(tk.END, f"Type: {global_var['type']}\n")
        if global_var['initial_value']:
            self.details_text.insert(tk.END, f"Initial Value: {global_var['initial_value']}\n")
        if global_var['comment']:
            self.details_text.insert(tk.END, f"Comment: {global_var['comment']}\n")

        type_details = global_var.get('type_details', {})
        if type_details:
            self.details_text.insert(tk.END, f"Type Category: {type_details.get('category', 'basic')}\n")
            if 'derived_from' in type_details:
                self.details_text.insert(tk.END, f"Derived From: {type_details['derived_from']}\n")

        # Add export button
        self._add_export_section(global_var)

    def _show_enum_details(self, enum_name):
        """Show details for an Enum"""
        enum = self._find_enum_by_name(enum_name)
        if not enum:
            self.details_text.insert(tk.END, f"Enum '{enum_name}' not found")
            return

        self.details_text.insert(tk.END, f"Enum: {enum_name}\n")
        self.details_text.insert(tk.END, f"Base Type: {enum.get('base_type', 'INT')}\n")
        self.details_text.insert(tk.END, "=" * 50 + "\n\n")

        values = enum.get('values', [])
        self.details_text.insert(tk.END, f"Values ({len(values)}):\n")
        for value in values:
            self.details_text.insert(tk.END, f"  {value['name']} = {value['value']}\n")

        # Add export button
        self._add_export_section(enum)

    def _show_union_details(self, union_name):
        """Show details for a Union"""
        union = self._find_union_by_name(union_name)
        if not union:
            self.details_text.insert(tk.END, f"Union '{union_name}' not found")
            return

        self.details_text.insert(tk.END, f"Union: {union_name}\n")
        self.details_text.insert(tk.END, "=" * 50 + "\n\n")

        members = union.get('members', [])
        self.details_text.insert(tk.END, f"Members ({len(members)}):\n")
        for member in members:
            self.details_text.insert(tk.END, f"  {member['name']} : {member['type']}\n")

        # Add export button
        self._add_export_section(union)

    def _show_structure_details(self, structure_name):
        """Show details for a Structure"""
        self.logger.debug(f"Showing details for Structure: {structure_name}")

        structure = self._find_structure_by_name(structure_name)
        if not structure:
            self.details_text.insert(tk.END, f"Structure '{structure_name}' not found")
            return

        self.details_text.insert(tk.END, f"Structure: {structure_name}\n")
        self.details_text.insert(tk.END, "=" * 50 + "\n\n")

        members = structure.get('members', [])
        self.details_text.insert(tk.END, f"Members ({len(members)}):\n")
        for member in members:
            self.details_text.insert(tk.END, f"  {member['name']} : {member['type']}\n")
            type_details = member.get('type_details', {})
            if type_details.get('category') == 'string' and 'length' in type_details.get('details', {}):
                self.details_text.insert(tk.END, f"    (Length: {type_details['details']['length']})\n")

        # Add export button
        self._add_export_section(structure)

    def _show_structure_member_details(self, member_name, tree, item_id):
        """Show details for a selected Structure Member"""
        self.logger.debug(f"Showing details for Structure Member: {member_name}")

        # Get the structure name
        struct_id = tree.parent(item_id)  # parent of members is the structure
        struct_name = tree.item(struct_id, 'text')

        structure = self._find_structure_by_name(struct_name)
        if not structure:
            self.details_text.insert(tk.END, f"Parent Structure '{struct_name}' not found")
            return

        members = structure.get('members', [])
        for member in members:
            if member['name'] == member_name:
                self.details_text.insert(tk.END, f"Structure Member: {member_name}\n")
                self.details_text.insert(tk.END, f"Parent Structure: {struct_name}\n")
                self.details_text.insert(tk.END, "=" * 50 + "\n\n")

                self.details_text.insert(tk.END, f"Type: {member['type']}\n")

                type_details = member.get('type_details', {})
                if type_details:
                    self.details_text.insert(tk.END, f"Type Category: {type_details.get('category', 'basic')}\n")
                    if type_details.get('category') == 'string' and 'length' in type_details.get('details', {}):
                        self.details_text.insert(tk.END, f"String Length: {type_details['details']['length']}\n")
                    if 'derived_from' in type_details:
                        self.details_text.insert(tk.END, f"Derived From: {type_details['derived_from']}\n")

                if member['initial_value']:
                    self.details_text.insert(tk.END, f"Initial Value: {member['initial_value']}\n")

                if member['comment']:
                    self.details_text.insert(tk.END, f"Comment: {member['comment']}\n")

                break

    def _show_enum_value_details(self, value_name, tree, item_id):
        """Show details for an Enum Value"""
        # Get the enum name
        enum_id = tree.parent(item_id)  # parent of values is the enum
        enum_name = tree.item(enum_id, 'text')

        enum = self._find_enum_by_name(enum_name)
        if not enum:
            self.details_text.insert(tk.END, f"Parent Enum '{enum_name}' not found")
            return

        values = enum.get('values', [])
        for value in values:
            if value['name'] == value_name:
                self.details_text.insert(tk.END, f"Enum Value: {value_name}\n")
                self.details_text.insert(tk.END, f"Parent Enum: {enum_name}\n")
                self.details_text.insert(tk.END, "=" * 50 + "\n\n")

                self.details_text.insert(tk.END, f"Value: {value.get('value', 'Not specified')}\n")

                details = value.get('details', {})
                if details:
                    self.details_text.insert(tk.END, "Additional Details:\n")
                    for key, val in details.items():
                        self.details_text.insert(tk.END, f"  {key}: {val}\n")
                break

    def _show_union_member_details(self, member_name, tree, item_id):
        """Show details for a Union Member"""
        # Get the union name
        union_id = tree.parent(item_id)
        union_name = tree.item(union_id, 'text')

        union = self._find_union_by_name(union_name)
        if not union:
            self.details_text.insert(tk.END, f"Parent Union '{union_name}' not found")
            return

        members = union.get('members', [])
        for member in members:
            if member['name'] == member_name:
                self.details_text.insert(tk.END, f"Union Member: {member_name}\n")
                self.details_text.insert(tk.END, f"Parent Union: {union_name}\n")
                self.details_text.insert(tk.END, "=" * 50 + "\n\n")

                self._show_variable_details(member)
                break

    def _show_action_details(self, action_name, tree, item_id):
        """Show details for an Action"""
        # Get the POU name
        pou_id = tree.parent(item_id)
        pou_name = tree.item(pou_id, 'text')

        pou = self._find_pou_by_name(pou_name)
        if not pou:
            self.details_text.insert(tk.END, f"Parent POU '{pou_name}' not found")
            return

        actions = pou.get('actions', [])
        for action in actions:
            if action['name'] == action_name:
                self.details_text.insert(tk.END, f"Action: {action_name}\n")
                self.details_text.insert(tk.END, f"Parent POU: {pou_name}\n")
                self.details_text.insert(tk.END, "=" * 50 + "\n\n")

                details = action.get('details', {})
                if details.get('variables'):
                    self.details_text.insert(tk.END, f"Variables: {len(details['variables'])}\n")
                if details.get('implementation'):
                    self.details_text.insert(tk.END, "Has implementation code\n")
                break

    def _show_method_details(self, method_name, tree, item_id):
        """Show details for a Method"""
        # Get the POU name
        pou_id = tree.parent(item_id)
        pou_name = tree.item(pou_id, 'text')

        pou = self._find_pou_by_name(pou_name)
        if not pou:
            self.details_text.insert(tk.END, f"Parent POU '{pou_name}' not found")
            return

        methods = pou.get('methods', [])
        for method in methods:
            if method['name'] == method_name:
                self.details_text.insert(tk.END, f"Method: {method_name}\n")
                self.details_text.insert(tk.END, f"Parent POU: {pou_name}\n")
                self.details_text.insert(tk.END, "=" * 50 + "\n\n")

                details = method.get('details', {})
                if details.get('variables'):
                    self.details_text.insert(tk.END, f"Variables: {len(details['variables'])}\n")
                if details.get('implementation'):
                    self.details_text.insert(tk.END, "Has implementation code\n")
                break

    def _show_pou_variable_details(self, var_name, tree, item_id):
        """Show details for a POU Variable"""
        # Get the POU name
        pou_id = tree.parent(item_id)
        pou_name = tree.item(pou_id, 'text')

        pou = self._find_pou_by_name(pou_name)
        if not pou:
            self.details_text.insert(tk.END, f"Parent POU '{pou_name}' not found")
            return

        details = pou.get('details', {})
        variables = details.get('variables', [])
        for var in variables:
            if var['name'] == var_name:
                self.details_text.insert(tk.END, f"POU Variable: {var_name}\n")
                self.details_text.insert(tk.END, f"Parent POU: {pou_name}\n")
                self.details_text.insert(tk.END, "=" * 50 + "\n\n")

                self._show_variable_details(var)
                break

    def _show_variable_details(self, var):
        """Show common variable details"""
        self.details_text.insert(tk.END, f"Type: {var['type']}\n")

        type_details = var.get('type_details', {})
        if type_details:
            self.details_text.insert(tk.END, f"Type Category: {type_details.get('category', 'basic')}\n")
            if type_details.get('category') == 'string' and 'length' in type_details.get('details', {}):
                self.details_text.insert(tk.END, f"String Length: {type_details['details']['length']}\n")
            if 'derived_from' in type_details:
                self.details_text.insert(tk.END, f"Derived From: {type_details['derived_from']}\n")

        if var['initial_value']:
            self.details_text.insert(tk.END, f"Initial Value: {var['initial_value']}\n")

        if var['comment']:
            self.details_text.insert(tk.END, f"Comment: {var['comment']}\n")

    # Search methods
    def _find_datatype_by_name(self, name):
        if not self.json_data:
            return None
        for dt in self.json_data.get('DataTypes', []):
            if dt['name'] == name:
                return dt
        return None

    def _find_pou_by_name(self, name):
        if not self.json_data:
            return None
        for pou in self.json_data.get('POUs', []):
            if pou['name'] == name:
                return pou
        return None

    def _find_global_var_by_name(self, name):
        if not self.json_data:
            return None
        for gv in self.json_data.get('GlobalVariables', []):
            if gv['name'] == name:
                return gv
        return None

    def _find_enum_by_name(self, name):
        if not self.json_data:
            return None
        for enum in self.json_data.get('Enums', []):
            if enum['name'] == name:
                return enum
        return None

    def _find_union_by_name(self, name):
        if not self.json_data:
            return None
        for union in self.json_data.get('Unions', []):
            if union['name'] == name:
                return union
        return None

    def _find_structure_by_name(self, name):
        if not self.json_data:
            return None
        for struct in self.json_data.get('Structures', []):
            if struct['name'] == name:
                return struct
        return None

    # Export functionality
    def _add_export_section(self, item_data):
        """Add export section to details view"""
        self.details_text.insert(tk.END, "\n" + "=" * 50 + "\n")
        self.details_text.insert(tk.END, "EXPORT OPTIONS:\n\n")

        # Create a temporary frame for buttons (this is a workaround since we can't embed widgets in Text)
        # In a real implementation, you might want to use a separate frame next to the text widget
        self.details_text.insert(tk.END, "To export complete structure documentation:\n")
        self.details_text.insert(tk.END, "1. Use the main menu Export option\n")
        self.details_text.insert(tk.END, "2. Or call export from command line\n")
        self.details_text.insert(tk.END, f"3. Item: {item_data['name']} (Type: {item_data.get('type', 'unknown')})\n")

    def export_item_structure(self, item_name, item_type, output_format='text'):
        """Export the complete structure of an item"""
        try:
            from export_networkx import NetworkXExporter

            if not self.json_data:
                self.logger.error("No JSON data available for export")
                return None

            # Create exporter and generate documentation
            exporter = NetworkXExporter(self.json_data)
            graph = exporter.export_item_structure(item_name, item_type)

            # Ask for save location
            filename = filedialog.asksaveasfilename(
                title=f"Export {item_name} Structure",
                defaultextension=f".{output_format}",
                filetypes=[(f"{output_format.upper()} files", f"*.{output_format}"), ("All files", "*.*")]
            )

            if filename:
                exporter.export_to_file(graph, filename, output_format)
                self.logger.info(f"Exported {item_name} structure to {filename}")
                return filename

        except ImportError as e:
            self.logger.error(f"NetworkX export module not available: {e}")
        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}", exc_info=True)

        return None