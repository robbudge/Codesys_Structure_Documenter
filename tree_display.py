"""
Tree display manager for showing structured data
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, List, Optional

from data_models import *

class TreeDisplayManager:
    """Manages tree display of XML export data"""

    def __init__(self, tree_widget, logger=None):
        self.tree = tree_widget
        self.logger = logger or logging.getLogger(__name__)
        self.xml_export = None

        # Configure tree columns
        self.tree.configure(columns=('type', 'details'))
        self.tree.heading('#0', text='Name')
        self.tree.heading('type', text='Type')
        self.tree.heading('details', text='Details')

        self.tree.column('#0', width=300, minwidth=200)
        self.tree.column('type', width=150, minwidth=100)
        self.tree.column('details', width=250, minwidth=150)

    def display_xml_export(self, xml_export: XmlExport):
        """Display XML export data in tree"""
        self.xml_export = xml_export
        self.clear_tree()

        self.logger.debug(f"Displaying XML export with {xml_export.get_summary()['total_items']} items")

        # Add categories
        self._add_category("Data Types", xml_export.data_types, 'datatype')
        self._add_category("Enumerations", xml_export.enums, 'enum')
        self._add_category("Structures", xml_export.structures, 'structure')
        self._add_category("Unions", xml_export.unions, 'union')
        self._add_category("POUs", xml_export.pous, 'pou')
        self._add_category("Global Variables", xml_export.global_variables, 'globalvar')

        # Expand main categories
        for child in self.tree.get_children(''):
            self.tree.item(child, open=True)

    def _add_category(self, category_name, items, item_type):
        """Add a category to the tree"""
        if not items:
            return

        category_id = self.tree.insert('', 'end',
                                     text=category_name,
                                     values=('Category', f'{len(items)} items'),
                                     tags=('category',))

        for item in items:
            self._add_item(category_id, item, item_type)

    def _add_item(self, parent_id, item, item_type):
        """Add an item to the tree"""
        if item_type == 'datatype' and isinstance(item, DataType):
            details = f"Base: {item.base_type}"
            if item.initial_value:
                details += f", Init: {item.initial_value}"

            item_id = self.tree.insert(parent_id, 'end',
                                     text=item.name,
                                     values=('Data Type', details),
                                     tags=('datatype',))

        elif item_type == 'enum' and isinstance(item, EnumType):
            details = f"Values: {len(item.values)}, Base: {item.base_type}"

            item_id = self.tree.insert(parent_id, 'end',
                                     text=item.name,
                                     values=('Enum', details),
                                     tags=('enum',))

            # Add enum values as children
            if item.values:
                values_id = self.tree.insert(item_id, 'end',
                                           text='Values',
                                           values=('Sub-category', f'{len(item.values)} items'),
                                           tags=('subcategory',))

                for value in item.values:
                    value_details = f"Value: {value.value}"
                    if value.description:
                        value_details += f", {value.description}"

                    self.tree.insert(values_id, 'end',
                                   text=value.name,
                                   values=('Enum Value', value_details),
                                   tags=('enumvalue',))

        elif item_type in ['structure', 'union'] and isinstance(item, StructureType):
            type_name = 'Structure' if item_type == 'structure' else 'Union'
            details = f"Members: {len(item.members)}"

            item_id = self.tree.insert(parent_id, 'end',
                                     text=item.name,
                                     values=(type_name, details),
                                     tags=(item_type,))

            # Add members as children
            if item.members:
                members_id = self.tree.insert(item_id, 'end',
                                            text='Members',
                                            values=('Sub-category', f'{len(item.members)} items'),
                                            tags=('subcategory',))

                for member in item.members:
                    member_details = f"Type: {member.type}"
                    if member.initial_value:
                        member_details += f", Init: {member.initial_value}"

                    self.tree.insert(members_id, 'end',
                                   text=member.name,
                                   values=('Member', member_details),
                                   tags=('member',))

        elif item_type == 'pou' and isinstance(item, Pou):
            details = f"Type: {item.pou_type.value}, Return: {item.return_type}"

            item_id = self.tree.insert(parent_id, 'end',
                                     text=item.name,
                                     values=('POU', details),
                                     tags=('pou',))

            # Add variables as children
            if item.variables:
                vars_id = self.tree.insert(item_id, 'end',
                                         text='Variables',
                                         values=('Sub-category', f'{len(item.variables)} items'),
                                         tags=('subcategory',))

                for var in item.variables:
                    var_details = f"Type: {var.type}"
                    if var.initial_value:
                        var_details += f", Init: {var.initial_value}"

                    self.tree.insert(vars_id, 'end',
                                   text=var.name,
                                   values=('Variable', var_details),
                                   tags=('variable',))

        elif item_type == 'globalvar' and isinstance(item, GlobalVariable):
            details = f"Type: {item.type}"
            if item.initial_value:
                details += f", Init: {item.initial_value}"

            self.tree.insert(parent_id, 'end',
                           text=item.name,
                           values=('Global Variable', details),
                           tags=('globalvar',))

    def get_selected_item(self):
        """Get currently selected item"""
        selected = self.tree.selection()
        if not selected:
            return None

        item_id = selected[0]
        item = self.tree.item(item_id)

        return {
            'id': item_id,
            'text': item.get('text', ''),
            'values': item.get('values', []),
            'tags': item.get('tags', [])
        }

    def clear_tree(self):
        """Clear all items from tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def expand_all(self):
        """Expand all tree items"""
        for item in self.tree.get_children(''):
            self._expand_recursive(item)

    def _expand_recursive(self, item_id):
        """Recursively expand tree items"""
        self.tree.item(item_id, open=True)
        for child in self.tree.get_children(item_id):
            self._expand_recursive(child)

    def collapse_all(self):
        """Collapse all tree items"""
        for item in self.tree.get_children(''):
            self.tree.item(item, open=False)