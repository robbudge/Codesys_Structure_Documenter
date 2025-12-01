"""
Main GUI for Codesys XML Documentation Generator
"""

import tkinter as tk
from tkinter import ttk, filedialog
import logging
import os
from pathlib import Path
from datetime import datetime
import traceback

from data_models import *
from xml_parser import CodesysXmlParser
from tree_display import TreeDisplayManager
from export_manager import ExportManager
from uml_generator import UMLGenerator


class CodesysXmlDocumenter:
    """Main GUI application"""

    def __init__(self):
        self.logger = logging.getLogger('CodesysXMLDocGenerator.GUI')
        self.xml_parser = CodesysXmlParser(self.logger)
        self.xml_export = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("Codesys PLCopen XML Documentation Generator")
        self.root.geometry("1200x800")

        self._setup_gui()
        self.logger.info("GUI initialized")

    def _setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="1. XML File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="XML File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60, state='readonly')
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(file_frame, text="Browse", command=self._browse_file).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(file_frame, text="Load & Parse", command=self._load_and_parse).grid(row=0, column=3)

        # Information panel
        info_frame = ttk.LabelFrame(main_frame, text="2. Export Information", padding="5")
        info_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Info grid
        ttk.Label(info_frame, text="Export Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.export_type_var = tk.StringVar(value="Not loaded")
        ttk.Label(info_frame, textvariable=self.export_type_var, foreground="blue").grid(row=0, column=1, sticky=tk.W)

        ttk.Label(info_frame, text="Data Types:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.data_types_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.data_types_var).grid(row=0, column=3, sticky=tk.W)

        ttk.Label(info_frame, text="Enums:").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        self.enums_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.enums_var).grid(row=0, column=5, sticky=tk.W)

        ttk.Label(info_frame, text="POUs:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.pous_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.pous_var).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(info_frame, text="Structures:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
        self.structures_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.structures_var).grid(row=1, column=3, sticky=tk.W)

        ttk.Label(info_frame, text="Unions:").grid(row=1, column=4, sticky=tk.W, padx=(20, 5))
        self.unions_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.unions_var).grid(row=1, column=5, sticky=tk.W)

        ttk.Label(info_frame, text="Total Items:").grid(row=1, column=6, sticky=tk.W, padx=(20, 5))
        self.total_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.total_var, font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=7,
                                                                                                   sticky=tk.W)

        # Tree display
        tree_frame = ttk.LabelFrame(main_frame, text="3. Structure Browser", padding="5")
        tree_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Tree with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.tree = ttk.Treeview(tree_frame, columns=('type', 'details'),
                                 show='tree headings', yscrollcommand=tree_scroll.set)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tree_scroll.config(command=self.tree.yview)

        # Initialize tree display manager
        self.tree_display = TreeDisplayManager(self.tree, self.logger)

        # Right-click menu
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="Export Item", command=self._export_selected_item)
        self.tree_menu.add_command(label="Expand All", command=self.tree_display.expand_all)
        self.tree_menu.add_command(label="Collapse All", command=self.tree_display.collapse_all)
        self.tree.bind("<Button-3>", self._show_tree_menu)

        # Details panel
        details_frame = ttk.LabelFrame(main_frame, text="4. Item Details", padding="5")
        details_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        details_frame.columnconfigure(0, weight=1)

        self.details_text = tk.Text(details_frame, height=10, wrap=tk.WORD)
        details_scroll = ttk.Scrollbar(details_frame, command=self.details_text.yview)
        self.details_text.config(yscrollcommand=details_scroll.set)

        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Export options
        export_frame = ttk.LabelFrame(main_frame, text="5. Export Options", padding="5")
        export_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        # In the export_frame section, add:
        ttk.Button(export_frame, text="Export UML",
                   command=self._export_uml_for_selected).grid(row=0, column=4, padx=5)
        ttk.Label(export_frame, text="Format:").grid(row=0, column=0, padx=(0, 5))
        self.format_var = tk.StringVar(value="html")
        format_combo = ttk.Combobox(export_frame, textvariable=self.format_var,
                                    values=["text", "html", "json"], state="readonly", width=10)
        format_combo.grid(row=0, column=1, padx=(0, 10))

        ttk.Button(export_frame, text="Export Selected",
                   command=self._export_selected_item).grid(row=0, column=2, padx=5)
        ttk.Button(export_frame, text="Export All",
                   command=self._export_all).grid(row=0, column=3, padx=5)
        # In the export_frame section, replace or add:
        ttk.Label(export_frame, text="UML Format:").grid(row=0, column=4, padx=(10, 5))

        # Create a frame for UML buttons
        uml_frame = ttk.Frame(export_frame)
        uml_frame.grid(row=0, column=5, padx=5)

        # Create buttons for different UML formats
        ttk.Button(uml_frame, text="Flowchart",
                   command=lambda: self._export_uml_for_selected("flowchart"),
                   width=10).grid(row=0, column=0, padx=2)
        ttk.Button(uml_frame, text="ER Diagram",
                   command=lambda: self._export_uml_for_selected("er"),
                   width=10).grid(row=0, column=1, padx=2)
        ttk.Button(uml_frame, text="Class Diagram",
                   command=lambda: self._export_uml_for_selected("class"),
                   width=10).grid(row=0, column=2, padx=2)

        # Add tooltips if you want
        self._create_tooltip(uml_frame, "Export UML diagrams in different formats")

        # Status bar
        self.status_var = tk.StringVar(value="Ready to load XML file")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

    def _browse_file(self):
        """Browse for XML file"""
        filename = filedialog.askopenfilename(
            title="Select Codesys PLCopen XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self.logger.info(f"Selected file: {filename}")

    def _load_and_parse(self):
        """Load and parse the XML file"""
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            self.logger.warning("Please select a valid XML file.")
            self.status_var.set("Error: Please select a valid XML file.")
            return

        self.status_var.set("Parsing XML file...")
        self.root.update()

        try:
            # Parse XML file
            self.xml_export = self.xml_parser.parse_file(file_path)

            # Update information display
            export_type_str = self.xml_export.export_type.value.upper()
            self.export_type_var.set(export_type_str)
            self.logger.info(f"Export type: {export_type_str}")

            summary = self.xml_export.get_summary()
            self.data_types_var.set(str(summary['data_types']))
            self.enums_var.set(str(summary['enums']))
            self.pous_var.set(str(summary['pous']))
            self.structures_var.set(str(summary['structures']))
            self.unions_var.set(str(summary['unions']))
            self.total_var.set(str(summary['total_items']))

            # Display in tree
            self.tree_display.display_xml_export(self.xml_export)

            success_msg = f"Loaded {summary['total_items']} items successfully ({export_type_str})"
            self.status_var.set(success_msg)
            self.logger.info(success_msg)

        except Exception as e:
            error_msg = f"Error parsing XML file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.status_var.set(f"Error: {str(e)}")

    def _on_tree_select(self, event):
        """Handle tree selection"""
        selected = self.tree_display.get_selected_item()
        if not selected:
            return

        # Clear details
        self.details_text.delete('1.0', tk.END)

        # Show basic info
        self.details_text.insert(tk.END, f"Name: {selected['text']}\n")
        self.details_text.insert(tk.END, f"Type: {selected['values'][0] if selected['values'] else 'Unknown'}\n")

        if len(selected['values']) > 1:
            self.details_text.insert(tk.END, f"Details: {selected['values'][1]}\n")

    def _show_tree_menu(self, event):
        """Show right-click menu on tree"""
        try:
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.tree_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.debug(f"Error showing tree menu: {str(e)}")

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget (simple version)"""
        # This is a simple implementation - you can enhance it if needed
        widget.bind('<Enter>', lambda e: self.status_var.set(text))
        widget.bind('<Leave>', lambda e: self.status_var.set(""))




    def _add_type_to_export(self, type_data, temp_export):
        """Add a type to the export if not already present"""
        if isinstance(type_data, EnumType):
            if not any(e.name == type_data.name for e in temp_export.enums):
                temp_export.enums.append(type_data)
        elif isinstance(type_data, StructureType):
            if type_data.is_union:
                if not any(u.name == type_data.name for u in temp_export.unions):
                    temp_export.unions.append(type_data)
            else:
                if not any(s.name == type_data.name for s in temp_export.structures):
                    temp_export.structures.append(type_data)
        elif isinstance(type_data, DataType):
            if not any(d.name == type_data.name for d in temp_export.data_types):
                temp_export.data_types.append(type_data)

    def _find_item_data(self, selected_item):
        """Find the data object for the selected tree item"""
        if not self.xml_export:
            return None

        item_name = selected_item['text']
        tags = selected_item['tags']

        if 'enum' in tags:
            for enum in self.xml_export.enums:
                if enum.name == item_name:
                    return enum

        elif 'datatype' in tags:
            for data_type in self.xml_export.data_types:
                if data_type.name == item_name:
                    return data_type

        elif 'structure' in tags:
            for structure in self.xml_export.structures:
                if structure.name == item_name:
                    return structure

        elif 'union' in tags:
            for union in self.xml_export.unions:
                if union.name == item_name:
                    return union

        elif 'pou' in tags:
            for pou in self.xml_export.pous:
                if pou.name == item_name:
                    return pou

        elif 'globalvar' in tags:
            for global_var in self.xml_export.global_variables:
                if global_var.name == item_name:
                    return global_var

        return None

    def _export_all(self):
        """Export all items"""
        if not self.xml_export:
            self.logger.warning("No data loaded. Please load an XML file first.")
            self.status_var.set("Warning: No data loaded. Please load an XML file first.")
            return

        # Get export format
        format_choice = self.format_var.get().lower()

        # Get output directory
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)

        # Export using ExportManager
        export_manager = ExportManager(self.logger)

        try:
            self.status_var.set("Starting export of all items...")
            self.root.update()

            # RESOLVE TYPE REFERENCES FIRST
            self.logger.debug("Resolving all type references...")
            self.xml_export.resolve_all_type_references()

            # Export everything
            exported_files = export_manager.export_all(self.xml_export, str(output_dir), format_choice)

            if exported_files:
                success_msg = f"Exported {len(exported_files)} files successfully to exports folder"
                self.logger.info(success_msg)
                self.status_var.set(success_msg)

                # Log summary
                summary = self.xml_export.get_summary()
                self.logger.info(f"Export summary:")
                self.logger.info(f"  - Unions: {summary['unions']}")
                self.logger.info(f"  - Structures: {summary['structures']}")
                self.logger.info(f"  - Enums: {summary['enums']}")
                self.logger.info(f"  - POUs: {summary['pous']}")
                self.logger.info(f"  - Data Types: {summary['data_types']}")
                self.logger.info(f"  - Global Variables: {summary['global_variables']}")
            else:
                error_msg = f"Export failed: {export_manager.error_count} errors"
                self.logger.error(error_msg)
                self.status_var.set(error_msg)

        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.status_var.set(f"Error: {str(e)}")

    def _open_file(self, filepath):
        """Open a file with default application"""
        try:
            import os
            import sys
            import subprocess

            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':
                subprocess.call(['open', filepath])
            else:
                subprocess.call(['xdg-open', filepath])
        except Exception as e:
            self.logger.debug(f"Could not open file {filepath}: {str(e)}")

    def _export_selected_item(self):
        """Export only the selected item"""
        selected = self.tree_display.get_selected_item()
        if not selected:
            self.logger.warning("Please select an item to export.")
            self.status_var.set("Warning: Please select an item to export.")
            return

        # Check if it's an exportable item (not a category)
        tags = selected['tags']
        if 'category' in tags or 'subcategory' in tags:
            self.logger.warning("Please select a specific item, not a category.")
            self.status_var.set("Warning: Please select a specific item, not a category.")
            return

        # Find the actual data object
        item_data = self._find_item_data(selected)
        if not item_data:
            self.logger.error("Could not find data for selected item.")
            self.status_var.set("Error: Could not find data for selected item.")
            return

        # Get export format
        format_choice = self.format_var.get().lower()

        # Get output directory
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)

        # Create a temporary XmlExport with only the selected item
        temp_export = XmlExport(
            export_type=self.xml_export.export_type,
            file_path=self.xml_export.file_path
        )

        # Add the selected item to temp_export FIRST
        item_type = None
        if isinstance(item_data, StructureType):
            if item_data.is_union:
                temp_export.unions.append(item_data)
                item_type = 'union'
                self.logger.debug(f"Added union {item_data.name} to temp_export")
            else:
                temp_export.structures.append(item_data)
                item_type = 'structure'
                self.logger.debug(f"Added structure {item_data.name} to temp_export")
        elif isinstance(item_data, EnumType):
            temp_export.enums.append(item_data)
            item_type = 'enum'
            self.logger.debug(f"Added enum {item_data.name} to temp_export")
        elif isinstance(item_data, Pou):
            temp_export.pous.append(item_data)
            item_type = 'pou'
            self.logger.debug(f"Added POU {item_data.name} to temp_export")
        elif isinstance(item_data, DataType):
            temp_export.data_types.append(item_data)
            item_type = 'datatype'
            self.logger.debug(f"Added data type {item_data.name} to temp_export")
        elif isinstance(item_data, GlobalVariable):
            temp_export.global_variables.append(item_data)
            item_type = 'globalvar'
            self.logger.debug(f"Added global variable {item_data.name} to temp_export")

        if not item_type:
            self.logger.error(f"Unknown item type: {type(item_data)}")
            self.status_var.set("Error: Unknown item type")
            return

        # Debug logging AFTER adding the main item
        self.logger.debug(f"Temp export after adding main item {item_data.name}:")
        self.logger.debug(f"  Unions: {len(temp_export.unions)}")
        self.logger.debug(f"  Structures: {len(temp_export.structures)}")
        self.logger.debug(f"  Enums: {len(temp_export.enums)}")
        self.logger.debug(f"  Data Types: {len(temp_export.data_types)}")

        # Also add any referenced types to the export so they can be resolved
        self._add_referenced_types(item_data, temp_export)

        # Debug logging AFTER adding referenced types
        self.logger.debug(f"Temp export after adding referenced types:")
        self.logger.debug(f"  Unions: {len(temp_export.unions)}")
        self.logger.debug(f"  Structures: {len(temp_export.structures)}")
        self.logger.debug(f"  Enums: {len(temp_export.enums)}")
        self.logger.debug(f"  Data Types: {len(temp_export.data_types)}")

        # Log what enums are in temp_export
        for enum in temp_export.enums:
            self.logger.debug(f"    Enum: {enum.name} with {len(enum.values)} values")

        # Log what unions are in temp_export
        for union in temp_export.unions:
            self.logger.debug(f"    Union: {union.name} with {len(union.members)} members")

        # Export using ExportManager
        export_manager = ExportManager(self.logger)

        try:
            # RESOLVE TYPE REFERENCES FIRST
            self.logger.debug(f"Resolving type references for {selected['text']}...")
            temp_export.resolve_all_type_references()

            # Export only this item
            self.status_var.set(f"Exporting {selected['text']}...")
            self.root.update()

            # Export the single item
            exported_files = export_manager.export_all(temp_export.to_dict(), str(output_dir))


            if exported_files.get('files') and len(exported_files['files']) > 0:
                first_file = exported_files['files'][0]
                success_msg = f"Exported {selected['text']} to {first_file.get('path', 'unknown')}"
            else:
                success_msg = f"Exported {selected['text']} but no files were created"


        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.status_var.set(f"Error: {str(e)}")

    def _add_referenced_types(self, item_data, temp_export):
        """Add referenced types to the export so they can be resolved"""
        if not self.xml_export:
            return

        # Get type registry from full export
        type_registry = self.xml_export.get_all_types()
        self.logger.debug(f"Full type registry has {len(type_registry)} total types")

        # Create a case-insensitive lookup
        type_lookup = {name.lower(): (name, type_obj) for name, type_obj in type_registry.items()}

        # Track types we've already added to avoid infinite recursion
        added_types = set()

        def add_type_recursive(type_name):
            """Recursively add types with case-insensitive matching"""
            if type_name in added_types:
                return

            # Try case-insensitive lookup
            lookup_key = type_name.lower()
            if lookup_key in type_lookup:
                actual_name, ref_type = type_lookup[lookup_key]
                self.logger.debug(
                    f"  Found type '{type_name}' -> actual name '{actual_name}' ({type(ref_type).__name__})")
                self._add_type_to_export(ref_type, temp_export)
                added_types.add(type_name)

                # If it's a structure/union, also add its member types
                if isinstance(ref_type, StructureType):
                    for member in ref_type.members:
                        if member.type and member.type.lower() != type_name.lower():
                            add_type_recursive(member.type)
            else:
                self.logger.debug(f"  Type '{type_name}' not found in registry (case-insensitive)")

        if isinstance(item_data, StructureType):
            self.logger.debug(f"Processing structure/union: {item_data.name} with {len(item_data.members)} members")
            # For structures/unions, add all member types
            for member in item_data.members:
                if member.type and member.type.lower() != item_data.name.lower():
                    self.logger.debug(f"  Looking for member type: {member.type}")
                    add_type_recursive(member.type)

        elif isinstance(item_data, Pou):
            # For POUs, add variable types
            for variable in item_data.variables:
                if variable.type:
                    add_type_recursive(variable.type)

    def _export_uml_for_selected(self, uml_format="flowchart"):
        """Export UML diagram for selected item in specified format"""
        selected = self.tree_display.get_selected_item()
        if not selected:
            self.logger.warning("Please select an item to export.")
            self.status_var.set("Warning: Please select an item to export.")
            return

        # Check if it's a structure, union, or enum
        tags = selected['tags']

        if 'union' not in tags and 'enum' not in tags and 'structure' not in tags:
            self.logger.warning("UML export is only available for structures, unions, or enums.")
            self.status_var.set("Warning: Please select a structure, union, or enum for UML export.")
            return

        # Find the actual data object
        item_data = self._find_item_data(selected)
        if not item_data:
            self.logger.error("Could not find data for selected item.")
            self.status_var.set("Error: Could not find data for selected item.")
            return

        # Get output directory based on format
        output_dir = Path(f"uml_exports_{uml_format}")
        output_dir.mkdir(exist_ok=True)

        try:
            # Import appropriate generator based on format
            if uml_format == "flowchart":
                from flowchart_generator import FlowchartGenerator
                generator = FlowchartGenerator(self.logger)
            elif uml_format == "er":
                from erdiagram_generator import ERDiagramGenerator
                generator = ERDiagramGenerator(self.logger)
            elif uml_format == "class":
                from classdiagram_generator import ClassDiagramGenerator
                generator = ClassDiagramGenerator(self.logger)
            else:
                self.logger.error(f"Unknown UML format: {uml_format}")
                self.status_var.set(f"Error: Unknown UML format: {uml_format}")
                return

            # Generate appropriate diagram based on item type
            if 'structure' in tags and isinstance(item_data, StructureType) and not item_data.is_union:
                self.status_var.set(f"Generating {uml_format} diagram for structure: {selected['text']}...")
                self.root.update()

                self.logger.info(f"Generating {uml_format} diagram for structure: {item_data.name}")

                # Call the appropriate generator method
                if hasattr(generator, 'generate_for_structure'):
                    html_file = generator.generate_for_structure(item_data, self.xml_export, output_dir)
                else:
                    self.logger.error(f"Generator doesn't support structure export: {type(generator).__name__}")
                    self.status_var.set(f"Error: Generator doesn't support structure export")
                    return

            elif 'union' in tags and isinstance(item_data, StructureType) and item_data.is_union:
                self.status_var.set(f"Generating {uml_format} diagram for union: {selected['text']}...")
                self.root.update()

                self.logger.info(f"Generating {uml_format} diagram for union: {item_data.name}")

                # Call the appropriate generator method
                if hasattr(generator, 'generate_for_union'):
                    html_file = generator.generate_for_union(item_data, self.xml_export, output_dir)
                else:
                    self.logger.error(f"Generator doesn't support union export: {type(generator).__name__}")
                    self.status_var.set(f"Error: Generator doesn't support union export")
                    return

            elif 'enum' in tags and isinstance(item_data, EnumType):
                self.status_var.set(f"Generating {uml_format} diagram for enum: {selected['text']}...")
                self.root.update()

                self.logger.info(f"Generating {uml_format} diagram for enum: {item_data.name}")

                # Call the appropriate generator method
                if hasattr(generator, 'generate_for_enum'):
                    html_file = generator.generate_for_enum(item_data, output_dir)
                else:
                    self.logger.error(f"Generator doesn't support enum export: {type(generator).__name__}")
                    self.status_var.set(f"Error: Generator doesn't support enum export")
                    return

            else:
                self.logger.warning(f"Selected item is not a supported type for UML export.")
                self.status_var.set("Warning: Selected item type not supported for UML export.")
                return

            if html_file and Path(html_file).exists():
                success_msg = f"Generated {uml_format} diagram: {html_file}"
                self.logger.info(success_msg)
                self.status_var.set(success_msg)

                # Option to open the file
                self._open_file(html_file)
            else:
                error_msg = f"Failed to generate {uml_format} diagram"
                self.logger.error(error_msg)
                self.status_var.set(f"Error: {error_msg}")

        except ImportError as e:
            error_msg = f"Failed to import {uml_format} generator: {str(e)}"
            self.logger.error(error_msg)
            self.status_var.set(f"Error: {uml_format} generator not available")
        except Exception as e:
            error_msg = f"{uml_format} generation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.status_var.set(f"Error: {str(e)}")
    def run(self):
        """Start the application"""
        self.root.mainloop()