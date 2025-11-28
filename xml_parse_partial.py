"""
Partial XML Parser for Codesys PLCopen XML exports
Enhanced parsing with better namespace handling and debugging
"""

import xml.etree.ElementTree as ET
import logging
import json
from pathlib import Path


class PartialXMLParser:
    """Parser for partial Codesys XML exports with enhanced debugging"""

    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        self.logger = logging.getLogger('CodesysXMLDocGenerator.PartialParser')
        self.logger.debug(f"PartialXMLParser initialized with file: {xml_file_path}")

        # Namespace handling - try multiple namespace approaches
        self.namespaces = {
            'ns': 'http://www.plcopen.org/xml/tc6_0200',
            '': 'http://www.plcopen.org/xml/tc6_0200'  # For no namespace
        }

        # Standardized data storage for JSON output
        self.data_types = []
        self.pous = []

        # Load and parse XML
        self._load_xml()

    def _load_xml(self):
        """Load and parse the XML file with enhanced error handling"""
        self.logger.debug(f"Loading XML file: {self.xml_file_path}")

        try:
            self.tree = ET.parse(self.xml_file_path)
            self.root = self.tree.getroot()

            # Debug: Log root tag and attributes
            self.logger.debug(f"XML Root: {self.root.tag}, Attributes: {self.root.attrib}")

            # Try to register namespaces for better parsing
            try:
                ET.register_namespace('', 'http://www.plcopen.org/xml/tc6_0200')
            except Exception as e:
                self.logger.debug(f"Namespace registration warning: {e}")

            self.logger.info("XML file parsed successfully")

        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Error loading XML file: {str(e)}", exc_info=True)
            raise

    def _find_with_fallback(self, element, path):
        """Find elements with namespace fallback"""
        # Try with namespace first
        result = element.find(path, self.namespaces)
        if result is not None:
            return result

        # Try without namespace
        result = element.find(path)
        if result is not None:
            self.logger.debug(f"Found element without namespace: {path}")
            return result

        # Try with wildcard namespace
        if '}' in path:
            # Convert ns:tag to *:tag
            wildcard_path = path.replace('ns:', '*:')
            result = element.find(wildcard_path)
            if result is not None:
                self.logger.debug(f"Found element with wildcard namespace: {path}")
                return result

        return None

    def _findall_with_fallback(self, element, path):
        """Find all elements with namespace fallback"""
        # Try with namespace first
        results = element.findall(path, self.namespaces)
        if results:
            return results

        # Try without namespace
        results = element.findall(path)
        if results:
            self.logger.debug(f"Found elements without namespace: {path} - count: {len(results)}")
            return results

        # Try with wildcard namespace
        if '}' in path:
            wildcard_path = path.replace('ns:', '*:')
            results = element.findall(wildcard_path)
            if results:
                self.logger.debug(f"Found elements with wildcard namespace: {path} - count: {len(results)}")
                return results

        return []

    def parse_to_json(self):
        """
        Parse the partial XML export and return standardized JSON

        Returns:
            dict: Standardized JSON structure with DataTypes and POUs
        """
        self.logger.debug("Starting enhanced XML parsing process for JSON output")

        try:
            # First, let's debug the XML structure
            self._debug_xml_structure()

            # Extract data types with multiple search strategies
            self._extract_data_types_enhanced()

            # Extract POUs with multiple search strategies
            self._extract_pous_enhanced()

            # Return standardized JSON
            json_data = self._get_standardized_json()

            self.logger.info(
                f"Enhanced parsing completed: {len(self.data_types)} data types, {len(self.pous)} POUs found")
            self.logger.debug(f"JSON summary: {json.dumps(json_data['summary'], indent=2)}")

            return json_data

        except Exception as e:
            self.logger.error(f"Error during enhanced XML parsing: {str(e)}", exc_info=True)
            raise

    def _debug_xml_structure(self):
        """Debug the XML structure to understand what's available"""
        self.logger.debug("=== XML STRUCTURE DEBUG ===")

        # Count all elements
        all_elements = list(self.root.iter())
        self.logger.debug(f"Total elements in XML: {len(all_elements)}")

        # Log unique element tags
        unique_tags = set()
        for elem in all_elements:
            unique_tags.add(elem.tag)

        self.logger.debug(f"Unique element tags: {list(unique_tags)[:20]}")  # First 20 tags

        # Look for types, dataTypes, pous at any level
        types_elems = self._findall_with_fallback(self.root, './/types')
        data_types_elems = self._findall_with_fallback(self.root, './/dataTypes')
        pous_elems = self._findall_with_fallback(self.root, './/pous')

        self.logger.debug(f"Found types elements: {len(types_elems)}")
        self.logger.debug(f"Found dataTypes elements: {len(data_types_elems)}")
        self.logger.debug(f"Found pous elements: {len(pous_elems)}")

        # If we found types, explore its children
        if types_elems:
            types_elem = types_elems[0]
            children_tags = [child.tag for child in types_elem]
            self.logger.debug(f"Children of types element: {children_tags}")

    def _extract_data_types_enhanced(self):
        """Enhanced data type extraction with multiple strategies"""
        self.logger.debug("Starting enhanced data type extraction")

        # Strategy 1: Look for dataTypes under types
        types_elems = self._findall_with_fallback(self.root, './/types')
        for types_elem in types_elems:
            data_types_elems = self._findall_with_fallback(types_elem, './dataTypes')
            for data_types_elem in data_types_elems:
                self._extract_data_types_from_element(data_types_elem)

        # Strategy 2: Look for dataTypes anywhere in document
        if not self.data_types:
            data_types_elems = self._findall_with_fallback(self.root, './/dataTypes')
            for data_types_elem in data_types_elems:
                self._extract_data_types_from_element(data_types_elem)

        # Strategy 3: Look for dataType elements directly
        if not self.data_types:
            data_type_elems = self._findall_with_fallback(self.root, './/dataType')
            self.logger.debug(f"Found {len(data_type_elems)} direct dataType elements")
            for data_type_elem in data_type_elems:
                self._process_data_type_element(data_type_elem)

        self.logger.info(f"Data type extraction completed: {len(self.data_types)} found")

    def _extract_data_types_from_element(self, data_types_elem):
        """Extract data types from a dataTypes element"""
        data_type_elems = self._findall_with_fallback(data_types_elem, './dataType')
        self.logger.debug(f"Found {len(data_type_elems)} dataType elements in dataTypes")

        for data_type in data_type_elems:
            self._process_data_type_element(data_type)

    def _process_data_type_element(self, data_type_elem):
        """Process individual data type element"""
        try:
            # Try multiple ways to find the name
            name = None

            # Method 1: Direct name element
            name_elem = self._find_with_fallback(data_type_elem, './name')
            if name_elem is not None and name_elem.text:
                name = name_elem.text
            else:
                # Method 2: Look for name in attributes or other locations
                if 'name' in data_type_elem.attrib:
                    name = data_type_elem.attrib['name']
                else:
                    # Method 3: Try to find any text content that might be the name
                    for child in data_type_elem:
                        if child.text and child.text.strip():
                            name = child.text.strip()
                            break

            if name:
                data_type_info = {
                    'name': name,
                    'type': 'dataType',
                    'details': self._extract_data_type_details(data_type_elem),
                    'element_debug': str(data_type_elem.tag)  # For debugging
                }
                self.data_types.append(data_type_info)
                self.logger.debug(f"Added data type: {name}")
            else:
                self.logger.warning(f"Could not extract name from dataType element: {data_type_elem.tag}")

        except Exception as e:
            self.logger.warning(f"Error processing data type element: {str(e)}")

    def _extract_pous_enhanced(self):
        """Enhanced POU extraction with multiple strategies"""
        self.logger.debug("Starting enhanced POU extraction")

        # Strategy 1: Look for pous under types
        types_elems = self._findall_with_fallback(self.root, './/types')
        for types_elem in types_elems:
            pous_elems = self._findall_with_fallback(types_elem, './pous')
            for pous_elem in pous_elems:
                self._extract_pous_from_element(pous_elem)

        # Strategy 2: Look for pous anywhere in document
        if not self.pous:
            pous_elems = self._findall_with_fallback(self.root, './/pous')
            for pous_elem in pous_elems:
                self._extract_pous_from_element(pous_elem)

        # Strategy 3: Look for pou elements directly
        if not self.pous:
            pou_elems = self._findall_with_fallback(self.root, './/pou')
            self.logger.debug(f"Found {len(pou_elems)} direct pou elements")
            for pou_elem in pou_elems:
                self._process_pou_element(pou_elem)

        self.logger.info(f"POU extraction completed: {len(self.pous)} found")

    def _extract_pous_from_element(self, pous_elem):
        """Extract POUs from a pous element"""
        pou_elems = self._findall_with_fallback(pous_elem, './pou')
        self.logger.debug(f"Found {len(pou_elems)} pou elements in pous")

        for pou in pou_elems:
            self._process_pou_element(pou)

    def _process_pou_element(self, pou_elem):
        """Process individual POU element"""
        try:
            # Try multiple ways to find the name
            name = None

            # Method 1: Direct name element
            name_elem = self._find_with_fallback(pou_elem, './name')
            if name_elem is not None and name_elem.text:
                name = name_elem.text
            else:
                # Method 2: Look for name in attributes
                if 'name' in pou_elem.attrib:
                    name = pou_elem.attrib['name']

            if name:
                pou_type = pou_elem.get('pouType', 'unknown')
                pou_info = {
                    'name': name,
                    'type': 'pou',
                    'pou_type': pou_type,
                    'details': self._extract_pou_details(pou_elem),
                    'element_debug': str(pou_elem.tag)  # For debugging
                }
                self.pous.append(pou_info)
                self.logger.debug(f"Added POU: {name} (type: {pou_type})")
            else:
                self.logger.warning(f"Could not extract name from pou element: {pou_elem.tag}")

        except Exception as e:
            self.logger.warning(f"Error processing POU element: {str(e)}")

    def _extract_data_type_details(self, data_type_elem):
        """Extract detailed information from data type element for JSON"""
        details = {}

        try:
            # Extract base type
            base_type_elem = self._find_with_fallback(data_type_elem, './baseType')
            if base_type_elem is not None:
                base_type_name = self._find_with_fallback(base_type_elem, './name')
                if base_type_name is not None and base_type_name.text:
                    details['base_type'] = base_type_name.text

            # Extract initial value
            initial_value_elem = self._find_with_fallback(data_type_elem, './initialValue')
            if initial_value_elem is not None:
                simple_value_elem = self._find_with_fallback(initial_value_elem, './simpleValue')
                if simple_value_elem is not None and simple_value_elem.text:
                    details['initial_value'] = simple_value_elem.text

            # Extract description/comment
            comment_elem = self._find_with_fallback(data_type_elem, './documentation/xhtml/p')
            if comment_elem is not None and comment_elem.text:
                details['description'] = comment_elem.text.strip()

            self.logger.debug(f"Extracted data type details: {list(details.keys())}")

        except Exception as e:
            self.logger.debug(f"Error extracting data type details: {str(e)}")

        return details

    def _extract_pou_details(self, pou_elem):
        """Extract detailed information from POU element for JSON"""
        details = {
            'variables': [],
            'implementation': None,
            'description': None
        }

        try:
            # Extract interface variables
            interface_elem = self._find_with_fallback(pou_elem, './interface')
            if interface_elem is not None:
                variables = self._findall_with_fallback(interface_elem, './variable')
                for var in variables:
                    var_info = self._extract_variable_info(var)
                    if var_info:
                        details['variables'].append(var_info)

            # Extract implementation
            implementation_elem = self._find_with_fallback(pou_elem, './implementation')
            if implementation_elem is not None:
                st_body_elem = self._find_with_fallback(implementation_elem, './ST')
                if st_body_elem is not None and st_body_elem.text:
                    details['implementation'] = st_body_elem.text.strip()

            # Extract description
            comment_elem = self._find_with_fallback(pou_elem, './documentation/xhtml/p')
            if comment_elem is not None and comment_elem.text:
                details['description'] = comment_elem.text.strip()

            self.logger.debug(
                f"Extracted POU details: {len(details['variables'])} variables, implementation: {'yes' if details['implementation'] else 'no'}")

        except Exception as e:
            self.logger.debug(f"Error extracting POU details: {str(e)}")

        return details

    def _extract_variable_info(self, var_elem):
        """Extract variable information for JSON"""
        try:
            name_elem = self._find_with_fallback(var_elem, './name')
            type_elem = self._find_with_fallback(var_elem, './type')
            initial_value_elem = self._find_with_fallback(var_elem, './initialValue')
            comment_elem = self._find_with_fallback(var_elem, './comment')

            if name_elem is None or not name_elem.text:
                return None

            type_name = 'UNKNOWN'
            if type_elem is not None:
                type_name_elem = self._find_with_fallback(type_elem, './name')
                if type_name_elem is not None and type_name_elem.text:
                    type_name = type_name_elem.text

            initial_value = ''
            if initial_value_elem is not None:
                simple_value_elem = self._find_with_fallback(initial_value_elem, './simpleValue')
                if simple_value_elem is not None and simple_value_elem.text:
                    initial_value = simple_value_elem.text

            comment = ''
            if comment_elem is not None and comment_elem.text:
                comment = comment_elem.text

            var_info = {
                'name': name_elem.text,
                'type': type_name,
                'initial_value': initial_value,
                'comment': comment
            }

            return var_info

        except Exception as e:
            self.logger.debug(f"Error extracting variable info: {str(e)}")
            return None

    def _get_standardized_json(self):
        """
        Return standardized JSON structure for GUI browsing

        Returns:
            dict: Standardized JSON with DataTypes and POUs
        """
        return {
            "source_file": Path(self.xml_file_path).name,
            "export_type": "type_a",
            "DataTypes": self.data_types,
            "POUs": self.pous,
            "summary": {
                "data_types_count": len(self.data_types),
                "pous_count": len(self.pous),
                "total_items": len(self.data_types) + len(self.pous)
            },
            "parsing_debug": {
                "xml_elements_analyzed": True,
                "enhanced_parsing_used": True
            }
        }


if __name__ == "__main__":
    print("This module is intended to be used with main.py")