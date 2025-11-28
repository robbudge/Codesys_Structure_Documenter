"""
Full XML Parser for Codesys PLCopen XML exports
Handles complete project exports with instances and configurations
Returns standardized format with DataTypes and POUs (ignores tasks)
"""

import xml.etree.ElementTree as ET
import logging
from pathlib import Path

class FullXMLParser:
    """Parser for full Codesys XML project exports"""

    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        self.logger = logging.getLogger('CodesysXMLDocGenerator.FullParser')
        self.logger.debug(f"FullXMLParser initialized with file: {xml_file_path}")

        # Namespace handling
        self.namespace = {'ns': 'http://www.plcopen.org/xml/tc6_0200'}

        # Standardized data storage - same format as partial parser
        self.data_types = []
        self.pous = []
        self.tree_structure = {}

        # Project information
        self.plc_name = None
        self.app_name = None

        # Load and parse XML
        self._load_xml()

    def _load_xml(self):
        """Load and parse the XML file"""
        self.logger.debug(f"Loading XML file: {self.xml_file_path}")

        try:
            self.tree = ET.parse(self.xml_file_path)
            self.root = self.tree.getroot()
            self.logger.info("XML file parsed successfully")

        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Error loading XML file: {str(e)}", exc_info=True)
            raise

    def parse(self):
        """
        Parse the full XML export and extract standardized DataTypes and POUs

        Returns:
            dict: Standardized tree structure with DataTypes and POUs
        """
        self.logger.debug("Starting full XML parsing process")

        try:
            # Extract project information
            self._extract_project_info()

            # Extract data types and POUs from the entire project
            self._extract_global_content()

            # Return standardized structure
            standardized_structure = self._get_standardized_structure()

            self.logger.info(f"Full parsing completed: {len(self.data_types)} data types, {len(self.pous)} POUs found")
            return standardized_structure

        except Exception as e:
            self.logger.error(f"Error during XML parsing: {str(e)}", exc_info=True)
            raise

    def _get_standardized_structure(self):
        """
        Return standardized structure matching partial parser format

        Returns:
            dict: Standardized structure with DataTypes and POUs
        """
        return {
            'DataTypes': self.data_types,
            'POUs': self.pous
        }

    def _extract_project_info(self):
        """Extract basic project information"""
        self.logger.debug("Extracting project information")

        # Extract project name
        project_info = self.root.find('.//ns:project', self.namespace)
        if project_info is not None:
            project_name_elem = project_info.find('.//ns:name', self.namespace)
            if project_name_elem is not None:
                self.logger.debug(f"Project name: {project_name_elem.text}")

        # Extract PLC and application names from instances
        instances_elem = self.root.find('.//ns:instances', self.namespace)
        if instances_elem is not None:
            configurations_elem = instances_elem.find('.//ns:configurations', self.namespace)
            if configurations_elem is not None:
                config_elem = configurations_elem.find('.//ns:configuration', self.namespace)
                if config_elem is not None:
                    config_name_elem = config_elem.find('.//ns:name', self.namespace)
                    if config_name_elem is not None:
                        self.plc_name = config_name_elem.text
                        self.logger.debug(f"PLC name: {self.plc_name}")

                    resource_elem = config_elem.find('.//ns:resource', self.namespace)
                    if resource_elem is not None:
                        resource_name_elem = resource_elem.find('.//ns:name', self.namespace)
                        if resource_name_elem is not None:
                            self.app_name = resource_name_elem.text
                            self.logger.debug(f"Application name: {self.app_name}")

    def _extract_global_content(self):
        """Extract data types and POUs from the entire project"""
        self.logger.debug("Extracting global content (DataTypes and POUs)")

        # Extract data types from the entire document
        self._extract_global_data_types()

        # Extract POUs from the entire document
        self._extract_global_pous()

        self.logger.debug(f"Global content extracted: {len(self.data_types)} data types, {len(self.pous)} POUs")

    def _extract_global_data_types(self):
        """Extract all data types from the project"""
        data_types_elems = self.root.findall('.//ns:dataType', self.namespace)
        self.logger.debug(f"Found {len(data_types_elems)} data type elements in project")

        for data_type in data_types_elems:
            try:
                name_elem = data_type.find('.//ns:name', self.namespace)
                if name_elem is not None:
                    # Check if we already have this data type (avoid duplicates)
                    if not any(dt['name'] == name_elem.text for dt in self.data_types):
                        data_type_info = {
                            'name': name_elem.text,
                            'type': 'dataType',
                            'element': data_type,
                            'details': self._extract_data_type_details(data_type)
                        }
                        self.data_types.append(data_type_info)
                        self.logger.debug(f"Added data type: {name_elem.text}")
            except Exception as e:
                self.logger.warning(f"Error processing data type: {str(e)}")
                continue

    def _extract_data_type_details(self, data_type_elem):
        """Extract detailed information from data type element"""
        details = {}

        try:
            # Extract base type
            base_type_elem = data_type_elem.find('.//ns:baseType', self.namespace)
            if base_type_elem is not None:
                base_type_name = base_type_elem.find('.//ns:name', self.namespace)
                if base_type_name is not None:
                    details['base_type'] = base_type_name.text

            # Extract initial value
            initial_value_elem = data_type_elem.find('.//ns:initialValue', self.namespace)
            if initial_value_elem is not None:
                simple_value_elem = initial_value_elem.find('.//ns:simpleValue', self.namespace)
                if simple_value_elem is not None and simple_value_elem.text:
                    details['initial_value'] = simple_value_elem.text

            # Extract description/comment
            comment_elem = data_type_elem.find('.//ns:documentation/ns:xhtml/ns:p', self.namespace)
            if comment_elem is not None and comment_elem.text:
                details['description'] = comment_elem.text

        except Exception as e:
            self.logger.debug(f"Error extracting data type details: {str(e)}")

        return details

    def _extract_global_pous(self):
        """Extract all POUs from the project"""
        pous_elems = self.root.findall('.//ns:pou', self.namespace)
        self.logger.debug(f"Found {len(pous_elems)} POU elements in project")

        for pou in pous_elems:
            try:
                name_elem = pou.find('.//ns:name', self.namespace)
                pou_type = pou.get('pouType', 'unknown')

                if name_elem is not None:
                    # Check if we already have this POU (avoid duplicates)
                    if not any(p['name'] == name_elem.text for p in self.pous):
                        pou_info = {
                            'name': name_elem.text,
                            'type': f'pou_{pou_type}',
                            'pou_type': pou_type,
                            'element': pou,
                            'details': self._extract_pou_details(pou)
                        }
                        self.pous.append(pou_info)
                        self.logger.debug(f"Added POU: {name_elem.text} (type: {pou_type})")
            except Exception as e:
                self.logger.warning(f"Error processing POU: {str(e)}")
                continue

    def _extract_pou_details(self, pou_elem):
        """Extract detailed information from POU element"""
        details = {
            'variables': [],
            'implementation': None
        }

        try:
            # Extract interface variables
            interface_elem = pou_elem.find('.//ns:interface', self.namespace)
            if interface_elem is not None:
                variables = interface_elem.findall('.//ns:variable', self.namespace)
                for var in variables:
                    var_info = self._extract_variable_info(var)
                    if var_info:
                        details['variables'].append(var_info)

            # Extract implementation
            implementation_elem = pou_elem.find('.//ns:implementation', self.namespace)
            if implementation_elem is not None:
                st_body_elem = implementation_elem.find('.//ns:ST', self.namespace)
                if st_body_elem is not None and st_body_elem.text:
                    details['implementation'] = st_body_elem.text.strip()

            # Extract description
            comment_elem = pou_elem.find('.//ns:documentation/ns:xhtml/ns:p', self.namespace)
            if comment_elem is not None and comment_elem.text:
                details['description'] = comment_elem.text

        except Exception as e:
            self.logger.debug(f"Error extracting POU details: {str(e)}")

        return details

    def _extract_variable_info(self, var_elem):
        """Extract variable information"""
        try:
            name_elem = var_elem.find('.//ns:name', self.namespace)
            type_elem = var_elem.find('.//ns:type', self.namespace)
            initial_value_elem = var_elem.find('.//ns:initialValue', self.namespace)
            comment_elem = var_elem.find('.//ns:comment', self.namespace)

            if name_elem is None:
                return None

            var_info = {
                'name': name_elem.text,
                'type': type_elem.find('.//ns:name', self.namespace).text if type_elem is not None else 'UNKNOWN',
                'initial_value': initial_value_elem.find('.//ns:simpleValue', self.namespace).text if initial_value_elem is not None else '',
                'comment': comment_elem.text if comment_elem is not None else ''
            }

            return var_info

        except Exception as e:
            self.logger.debug(f"Error extracting variable info: {str(e)}")
            return None

    def generate_documentation(self, selected_items, output_path):
        """
        Generate documentation for selected items

        Args:
            selected_items (list): List of selected tree items
            output_path (str): Output file path

        Returns:
            bool: Success status
        """
        self.logger.info(f"Generating documentation for {len(selected_items)} items to {output_path}")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Codesys PLCopen XML Documentation (Full Project Export)\n\n")
                f.write(f"Source: {Path(self.xml_file_path).name}\n")
                if self.plc_name:
                    f.write(f"PLC: {self.plc_name}\n")
                if self.app_name:
                    f.write(f"Application: {self.app_name}\n")
                f.write("\n")

                # Group selected items by type
                data_type_items = []
                pou_items = []

                for item in selected_items:
                    for level in item['hierarchy']:
                        if level['text'] == 'DataTypes':
                            data_type_items.append(item)
                            break
                        elif level['text'] == 'POUs':
                            pou_items.append(item)
                            break

                self.logger.debug(f"Documenting {len(data_type_items)} data types and {len(pou_items)} POUs")

                # Document data types
                if data_type_items:
                    f.write("## Data Types\n\n")
                    for item in data_type_items:
                        self._document_data_type(f, item)

                # Document POUs
                if pou_items:
                    f.write("## Program Organization Units (POUs)\n\n")
                    for item in pou_items:
                        self._document_pou(f, item)

                f.write(f"\n\n---\n*Documentation generated from full project export*")

            self.logger.info("Documentation generated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error generating documentation: {str(e)}", exc_info=True)
            return False

    def _document_data_type(self, file_obj, item):
        """Document a data type"""
        self.logger.debug(f"Documenting data type: {item['text']}")

        # Find the data type element
        data_type_info = None
        for dt in self.data_types:
            if dt['name'] == item['text']:
                data_type_info = dt
                break

        if not data_type_info:
            self.logger.warning(f"Data type {item['text']} not found in parsed data")
            return

        file_obj.write(f"### {item['text']}\n\n")

        try:
            details = data_type_info.get('details', {})

            if 'base_type' in details:
                file_obj.write(f"- **Base Type**: {details['base_type']}\n")

            if 'initial_value' in details:
                file_obj.write(f"- **Initial Value**: {details['initial_value']}\n")

            if 'description' in details:
                file_obj.write(f"- **Description**: {details['description']}\n")

            file_obj.write("\n")

        except Exception as e:
            self.logger.warning(f"Error documenting data type {item['text']}: {str(e)}")
            file_obj.write("*Error extracting details*\n\n")

    def _document_pou(self, file_obj, item):
        """Document a POU"""
        self.logger.debug(f"Documenting POU: {item['text']}")

        # Find the POU element
        pou_info = None
        for pou in self.pous:
            if pou['name'] == item['text']:
                pou_info = pou
                break

        if not pou_info:
            self.logger.warning(f"POU {item['text']} not found in parsed data")
            return

        file_obj.write(f"### {item['text']} ({pou_info['pou_type'].upper()})\n\n")

        try:
            details = pou_info.get('details', {})

            if 'description' in details:
                file_obj.write(f"**Description**: {details['description']}\n\n")

            # Document variables
            variables = details.get('variables', [])
            if variables:
                file_obj.write("#### Variables\n\n")
                file_obj.write("| Name | Type | Initial Value | Comment |\n")
                file_obj.write("|------|------|---------------|---------|\n")

                for var in variables:
                    file_obj.write(f"| {var['name']} | {var['type']} | {var['initial_value']} | {var['comment']} |\n")

                file_obj.write("\n")

            # Document implementation
            implementation = details.get('implementation')
            if implementation:
                file_obj.write("#### Implementation (ST)\n\n```st\n")
                file_obj.write(implementation)
                file_obj.write("\n```\n\n")

            file_obj.write("\n")

        except Exception as e:
            self.logger.warning(f"Error documenting POU {item['text']}: {str(e)}")
            file_obj.write("*Error extracting details*\n\n")

if __name__ == "__main__":
    print("This module is intended to be used with main.py")