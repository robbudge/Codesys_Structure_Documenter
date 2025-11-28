"""
Main GUI module for Codesys XML Parser using tkinter
Simplified version that delegates to specialized modules
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import logging
import os
import json
from pathlib import Path
from gui_tree_manager import TreeManager
from gui_details_manager import DetailsManager

class XMLParserGUI:
    """Main GUI for Codesys XML Parser with modular architecture"""

    def __init__(self, generator):
        self.generator = generator
        self.logger = logging.getLogger('CodesysXMLDocGenerator.GUI')
        self.logger.debug("XMLParserGUI initializing")

        # Initialize instance variables
        self.current_parser = None
        self.json_data = None
        self.selected_xml_file = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("Codesys PLCopen XML Documentation Generator - Modular Architecture")
        self.root.geometry("1200x900")

        self._setup_gui()
        self.logger.info("XMLParserGUI initialized successfully")

    def _setup_gui(self):
        """Setup the main GUI components"""
        self.logger.debug("Setting up main GUI components")

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="1. XML File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="XML File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state='readonly')
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(file_frame, text="Browse", command=self._browse_file).grid(row=0, column=2)
        ttk.Button(file_frame, text="Load & Parse XML", command=self._load_and_parse_xml).grid(row=0, column=3, padx=(5, 0))

        # Export button in file frame
        ttk.Button(file_frame, text="Export Selected Item", command=self.export_current_item).grid(row=0, column=4, padx=(10, 0))

        # XML info section
        info_frame = ttk.LabelFrame(main_frame, text="2. XML Information", padding="5")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Create a grid for info labels (2 rows, 4 columns)
        ttk.Label(info_frame, text="XML Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.xml_type_var = tk.StringVar(value="Not loaded")
        ttk.Label(info_frame, textvariable=self.xml_type_var, foreground="blue").grid(row=0, column=1, sticky=tk.W)

        ttk.Label(info_frame, text="Data Types:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.data_types_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.data_types_count_var).grid(row=0, column=3, sticky=tk.W)

        ttk.Label(info_frame, text="POUs:").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        self.pous_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.pous_count_var).grid(row=0, column=5, sticky=tk.W)

        ttk.Label(info_frame, text="Global Vars:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.global_vars_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.global_vars_count_var).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(info_frame, text="Enums:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
        self.enums_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.enums_count_var).grid(row=1, column=3, sticky=tk.W)

        ttk.Label(info_frame, text="Unions:").grid(row=1, column=4, sticky=tk.W, padx=(20, 5))
        self.unions_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.unions_count_var).grid(row=1, column=5, sticky=tk.W)

        ttk.Label(info_frame, text="Structures:").grid(row=1, column=6, sticky=tk.W, padx=(20, 5))
        self.structures_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.structures_count_var).grid(row=1, column=7, sticky=tk.W)

        # Tree view for content selection
        tree_frame = ttk.LabelFrame(main_frame, text="3. Browse Structure (Click to select, Double-click to expand)", padding="5")
        tree_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.tree = ttk.Treeview(tree_frame, columns=('type', 'details'), show='tree headings', yscrollcommand=tree_scroll.set)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure tree columns
        self.tree.heading('#0', text='Name')
        self.tree.heading('type', text='Type')
        self.tree.heading('details', text='Details')

        self.tree.column('#0', width=400)
        self.tree.column('type', width=150)
        self.tree.column('details', width=300)

        tree_scroll.config(command=self.tree.yview)

        # Details panel
        details_frame = ttk.LabelFrame(main_frame, text="4. Item Details", padding="5")
        details_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)

        self.details_text = tk.Text(details_frame, height=12, wrap=tk.WORD)
        details_scroll = ttk.Scrollbar(details_frame, command=self.details_text.yview)
        self.details_text.config(yscrollcommand=details_scroll.set)

        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Initialize managers
        self.tree_manager = TreeManager(self.tree, self.logger)
        self.details_manager = DetailsManager(self.details_text, self.logger)

        # Bind events
        self.tree.bind('<Double-1>', self._on_tree_double_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        # Status bar
        self.status_var = tk.StringVar(value="Ready to load XML file")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        self.logger.debug("Main GUI components setup completed")

    def _browse_file(self):
        """Browse for XML file"""
        self.logger.debug("File browse dialog opened")
        filename = filedialog.askopenfilename(
            title="Select Codesys PLCopen XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self.selected_xml_file = filename
            self.logger.info(f"Selected XML file: {filename}")

    def _load_and_parse_xml(self):
        """Load, parse the selected XML file and display in tree"""
        if not self.selected_xml_file:
            messagebox.showwarning("Warning", "Please select an XML file first.")
            return

        self.logger.info(f"Loading and parsing XML file: {self.selected_xml_file}")
        self.status_var.set("Loading and parsing XML file...")
        self.root.update()

        try:
            # Clear existing tree and details
            self.tree_manager.clear_tree()
            self.details_manager.clear_details()

            # Parse XML file and get JSON data
            self.current_parser, self.json_data = self.generator.parse_xml_file(self.selected_xml_file)

            # Update XML type information
            detection_result = self.generator.detect_xml_type_and_structure(self.selected_xml_file)
            xml_type = detection_result['type']
            self.xml_type_var.set(f"{xml_type.upper()} Export")

            # Update counts
            summary = self.json_data.get('summary', {})
            self.data_types_count_var.set(str(summary.get('data_types_count', 0)))
            self.pous_count_var.set(str(summary.get('pous_count', 0)))
            self.global_vars_count_var.set(str(summary.get('global_vars_count', 0)))
            self.enums_count_var.set(str(summary.get('enums_count', 0)))
            self.unions_count_var.set(str(summary.get('unions_count', 0)))
            self.structures_count_var.set(str(summary.get('structures_count', 0)))

            # Display JSON data in tree
            self.tree_manager.display_json_in_tree(self.json_data)

            # Update details manager with JSON data
            self.details_manager.set_json_data(self.json_data)

            self.status_var.set(f"XML parsed successfully - Ready for browsing")
            self.logger.info(f"XML parsed successfully, JSON data loaded")

        except Exception as e:
            error_msg = f"Error processing XML file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            messagebox.showerror("Error", error_msg)
            self.status_var.set("Error processing XML file")

    def _on_tree_double_click(self, event):
        """Handle tree double-click for expand/collapse"""
        self.tree_manager.handle_double_click(event)

    def _on_tree_select(self, event):
        """Handle tree item selection and display details"""
        try:
            selected_item = self.tree_manager.get_selected_item()
            if selected_item:
                self.details_manager.show_item_details(selected_item, self.tree_manager.tree)
        except Exception as e:
            error_msg = f"Error handling tree selection: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.details_manager.clear_details()
            self.details_manager.details_text.insert(tk.END, f"Error: {str(e)}")

    def export_current_item(self):
        """Export the currently selected item"""
        selected_item = self.tree_manager.get_selected_item()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an item to export.")
            return

        item_name = selected_item['text']
        item_tags = selected_item['tags']

        # Determine item type from tags
        item_type = None
        type_mapping = {
            'datatype': 'dataType',
            'pou': 'pou',
            'enum': 'enum',
            'union': 'union',
            'structure': 'structure',
            'globalvar': 'global_var'
        }

        for tag in item_tags:
            if tag in type_mapping:
                item_type = type_mapping[tag]
                break

        if not item_type:
            messagebox.showwarning("Warning",
                                "Selected item cannot be exported. Please select a:\n"
                                "- Data Type\n- POU\n- Enum\n- Union\n- Structure\n- Global Variable")
            return

        # Ask for format
        format_choice = simpledialog.askstring("Export Format",
                                             "Enter export format (text/html/json):",
                                             initialvalue="text")
        if format_choice and format_choice.lower() in ['text', 'html', 'json']:
            try:
                filename = self.details_manager.export_item_structure(item_name, item_type, format_choice.lower())
                if filename:
                    messagebox.showinfo("Export Successful", f"Documentation exported to:\n{filename}")
                else:
                    messagebox.showerror("Export Failed", "Failed to export documentation. Check logs for details.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Export failed: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Invalid format. Use 'text', 'html', or 'json'.")

    def run(self):
        """Start the GUI main loop"""
        self.logger.info("Starting GUI main loop")
        self.root.mainloop()
        self.logger.info("GUI main loop ended")

if __name__ == "__main__":
    print("This module is intended to be used with main.py")
