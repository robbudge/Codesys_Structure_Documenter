#!/usr/bin/env python3
"""
CODESYS XML Parser for structure and enum definitions
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import re
import datetime


class CodesysStructureParser:
    def __init__(self, xml_file_path: str, debug: bool = True):
        self.xml_file_path = xml_file_path
        self.debug_enabled = debug
        self.debug_info = []

        self._debug(f"Loading XML from: {xml_file_path}")
        try:
            self.tree = ET.parse(xml_file_path)
            self.root = self.tree.getroot()
            self._debug(f"Root tag: {self.root.tag}")
            self._debug(f"Root attributes: {self.root.attrib}")

            # Extract namespace from root tag
            if '}' in self.root.tag:
                self.namespace = self.root.tag.split('}')[0] + '}'
            else:
                self.namespace = ''
            self._debug(f"Detected namespace: '{self.namespace}'")

        except Exception as e:
            self._debug(f"ERROR loading XML: {e}", is_error=True)
            raise

        self.structures = {}
        self.enums = {}
        self.unions = {}

    def _debug(self, message: str, is_error: bool = False):
        """Add debug message with timestamp and originator info"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Get the calling function name for context
        import inspect
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name if caller_frame else "unknown"
        class_name = self.__class__.__name__

        debug_msg = f"[{timestamp}] [{class_name}.{caller_name}] {message}"

        if is_error:
            debug_msg = f"ERROR: {debug_msg}"

        self.debug_info.append(debug_msg)

        if self.debug_enabled:
            print(debug_msg)

    def get_debug_log(self) -> List[str]:
        """Get the complete debug log"""
        return self.debug_info

    def save_debug_log(self, file_path: str):
        """Save debug log to file"""
        with open(file_path, 'w') as f:
            for line in self.debug_info:
                f.write(line + '\n')
        self._debug(f"Debug log saved to: {file_path}")

    def _find_with_namespace(self, path: str) -> List[ET.Element]:
        """Find elements with namespace handling"""
        # Replace element names in path with namespaced versions
        elements = path.split('/')
        namespaced_path = ''

        for elem in elements:
            if elem == '':
                continue
            if elem.startswith('.'):
                namespaced_path += elem
            else:
                namespaced_path += f"{self.namespace}{elem}"
            namespaced_path += '/'

        # Remove trailing slash
        namespaced_path = namespaced_path.rstrip('/')

        self._debug(f"Searching with path: {namespaced_path}")
        return self.root.findall(namespaced_path)

    def _find_single_with_namespace(self, path: str) -> Optional[ET.Element]:
        """Find single element with namespace handling"""
        elements = self._find_with_namespace(path)
        return elements[0] if elements else None

    def parse_all_structures(self) -> Dict[str, Any]:
        """Parse all data types from CODESYS XML"""
        self._debug("Starting parsing...")

        # Reset collections
        self.structures = {}
        self.enums = {}
        self.unions = {}

        # First, let's explore the XML structure to understand what we're dealing with
        self._explore_xml_structure()

        # Parse types -> dataTypes section specifically
        types_section = self._find_single_with_namespace('types')
        if types_section is not None:
            self._debug("Found types section")
            data_types_section = types_section.find(f'{self.namespace}dataTypes')
            if data_types_section is not None:
                self._debug(f"Found dataTypes section with {len(data_types_section)} children")
                self._parse_data_types_section(data_types_section)
            else:
                self._debug("No dataTypes section found in types")
        else:
            self._debug("No types section found, searching for dataType elements directly")
            # Search for dataType elements anywhere in the document
            self._parse_data_type_elements()

        # Also look for pou elements which might contain structures
        self._parse_pou_elements()

        self._debug(
            f"Parsing complete: {len(self.structures)} structures, {len(self.enums)} enums, {len(self.unions)} unions")

        # Debug: Print what we found
        if self.enums:
            self._debug(f"Found enums: {list(self.enums.keys())}")
        if self.structures:
            self._debug(f"Found structures: {list(self.structures.keys())}")
        if self.unions:
            self._debug(f"Found unions: {list(self.unions.keys())}")

        return {
            'structures': self.structures,
            'enums': self.enums,
            'unions': self.unions
        }

    def _explore_xml_structure(self):
        """Explore the XML structure to understand what we're dealing with"""
        self._debug("Exploring XML structure...")

        # Count different element types with namespace handling
        data_types = self._find_with_namespace('.//dataType')
        pous = self._find_with_namespace('.//pou')
        structures = self._find_with_namespace('.//Structure')
        enums = self._find_with_namespace('.//Enumeration')

        # Also check the types -> dataTypes path specifically
        types_section = self._find_single_with_namespace('types')
        if types_section:
            self._debug("Found types section at root level")
            data_types_in_types = types_section.findall(f'{self.namespace}dataTypes')
            self._debug(f"Found {len(data_types_in_types)} dataTypes in types section")

            for data_types_elem in data_types_in_types:
                data_type_children = data_types_elem.findall(f'{self.namespace}dataType')
                self._debug(f"Found {len(data_type_children)} dataType elements in dataTypes")

                # Print first few names
                for i, dt in enumerate(data_type_children[:5]):
                    name = dt.get('name', 'UNNAMED')
                    self._debug(f"dataType in types/dataTypes[{i}]: name='{name}'")

        self._debug(f"Direct search found:")
        self._debug(f"  - dataType elements: {len(data_types)}")
        self._debug(f"  - pou elements: {len(pous)}")
        self._debug(f"  - Structure elements: {len(structures)}")
        self._debug(f"  - Enumeration elements: {len(enums)}")

    def _parse_data_types_section(self, data_types_section: ET.Element):
        """Parse the dataTypes section of the XML"""
        self._debug("Parsing dataTypes section")

        for data_type in data_types_section.findall(f'{self.namespace}dataType'):
            self._parse_single_data_type(data_type)

    def _parse_data_type_elements(self):
        """Parse dataType elements anywhere in the document"""
        self._debug("Searching for dataType elements")

        data_types = self._find_with_namespace('.//dataType')
        self._debug(f"Found {len(data_types)} dataType elements")

        for data_type in data_types:
            self._parse_single_data_type(data_type)

    def _parse_single_data_type(self, data_type: ET.Element):
        """Parse a single dataType element"""
        name = data_type.get('name')
        if not name:
            self._debug("Skipping unnamed dataType")
            return

        self._debug(f"Processing dataType: '{name}'")

        # Check for baseType first (this is where enums are typically defined)
        base_type = data_type.find(f'{self.namespace}baseType')
        if base_type is not None:
            self._debug(f"dataType '{name}' has baseType")
            self._parse_base_type(name, base_type, data_type)
        else:
            self._debug(f"dataType '{name}' has no baseType, checking for other content")
            # Try to infer type from content
            self._infer_type_from_content(name, data_type)

    def _parse_base_type(self, name: str, base_type: ET.Element, parent_element: ET.Element):
        """Parse the baseType element to determine the actual type"""
        self._debug(f"Analyzing baseType for '{name}'")

        # Look for enum in baseType
        enum_elem = base_type.find(f'{self.namespace}enum')
        if enum_elem is not None:
            self._debug(f"dataType '{name}' is an ENUM")
            self.enums[name] = self._parse_enum_element(name, enum_elem, parent_element)
            return

        # Look for struct in baseType
        struct_elem = base_type.find(f'{self.namespace}struct')
        if struct_elem is not None:
            self._debug(f"dataType '{name}' is a STRUCT")
            self.structures[name] = self._parse_struct_element(name, struct_elem, parent_element)
            return

        # Check for derived type
        derived_elem = base_type.find(f'{self.namespace}derived')
        if derived_elem is not None:
            derived_name = derived_elem.get('name')
            self._debug(f"dataType '{name}' is derived from '{derived_name}'")
            # Handle derived types if needed

        # If we get here, try to determine type from baseType attributes or content
        base_type_name = base_type.get('name', '').lower()
        if 'enum' in base_type_name:
            self._debug(f"dataType '{name}' appears to be enum based on baseType name")
            self.enums[name] = self._parse_enum_from_values(name, parent_element)
        elif 'struct' in base_type_name:
            self._debug(f"dataType '{name}' appears to be struct based on baseType name")
            # Try to parse as structure
            pass
        else:
            self._debug(f"dataType '{name}' has unknown baseType structure")

    def _parse_enum_element(self, name: str, enum_elem: ET.Element, parent_element: ET.Element) -> Dict[str, Any]:
        """Parse an enum element"""
        self._debug(f"Parsing enum '{name}'")

        enum_data = {
            'type': 'enum',
            'values': [],
            'comment': '',
            'base_type': 'enum'
        }

        # Parse enum values
        values_elem = enum_elem.find(f'{self.namespace}values')
        if values_elem is not None:
            for value_elem in values_elem.findall(f'{self.namespace}value'):
                value_name = value_elem.get('name')
                value_value = value_elem.get('value', '')

                if value_name:
                    enum_value = {
                        'name': value_name,
                        'value': value_value,
                        'comment': ''
                    }
                    enum_data['values'].append(enum_value)
                    self._debug(f"  Value: {value_name} = {value_value}")

        # Parse documentation if available
        self._parse_enum_documentation(name, parent_element, enum_data)

        self._debug(f"Enum '{name}' has {len(enum_data['values'])} values")
        return enum_data

    def _parse_enum_from_values(self, name: str, parent_element: ET.Element) -> Dict[str, Any]:
        """Parse enum from values found in the dataType element"""
        self._debug(f"Parsing enum '{name}' from values")

        enum_data = {
            'type': 'enum',
            'values': [],
            'comment': '',
            'base_type': 'enum'
        }

        # Look for values anywhere in the dataType
        values = parent_element.findall(f'.//{self.namespace}value')
        for value_elem in values:
            value_name = value_elem.get('name')
            value_value = value_elem.get('value', '')

            if value_name:
                enum_value = {
                    'name': value_name,
                    'value': value_value,
                    'comment': ''
                }
                enum_data['values'].append(enum_value)
                self._debug(f"  Value: {value_name} = {value_value}")

        # Parse documentation
        self._parse_enum_documentation(name, parent_element, enum_data)

        self._debug(f"Enum '{name}' has {len(enum_data['values'])} values")
        return enum_data

    def _parse_enum_documentation(self, name: str, parent_element: ET.Element, enum_data: Dict[str, Any]):
        """Parse enum value documentation"""
        self._debug(f"Looking for documentation for enum '{name}'")

        # Look for enum value documentation in addData
        add_data = parent_element.find(f'{self.namespace}addData')
        if add_data is not None:
            for data_elem in add_data.findall(f'{self.namespace}data'):
                data_name = data_elem.get('name', '')
                if 'enumvaluedocumentation' in data_name:
                    self._debug(f"Found enum value documentation for '{name}'")
                    self._parse_enum_value_documentation(data_elem, enum_data)

    def _parse_enum_value_documentation(self, data_elem: ET.Element, enum_data: Dict[str, Any]):
        """Parse detailed enum value documentation"""
        # Note: Documentation elements might not use the namespace
        doc_elem = data_elem.find('EnumValueDocumentation')
        if doc_elem is None:
            # Try with namespace
            doc_elem = data_elem.find(f'{self.namespace}EnumValueDocumentation')

        if doc_elem is not None:
            for enum_value_doc in doc_elem.findall('EnumValue'):
                value_name = enum_value_doc.findtext('Name', '')
                documentation = enum_value_doc.findtext('Documentation/xhtml', '')

                if value_name and documentation:
                    # Find this value in our enum data and add documentation
                    for value_data in enum_data['values']:
                        if value_data['name'] == value_name:
                            value_data['comment'] = documentation
                            self._debug(f"Added documentation for '{value_name}': {documentation[:50]}...")
                            break

    def _parse_struct_element(self, name: str, struct_elem: ET.Element, parent_element: ET.Element) -> Dict[str, Any]:
        """Parse a struct element"""
        self._debug(f"Parsing struct '{name}'")

        struct_data = {
            'type': 'structure',
            'members': [],
            'comment': '',
            'base_type': 'struct'
        }

        # Parse struct members (variables)
        variables = struct_elem.findall(f'{self.namespace}variable')
        for var_elem in variables:
            member = self._parse_variable(var_elem)
            if member:
                struct_data['members'].append(member)
                self._debug(f"  Member: {member['name']} : {member['type']}")

        self._debug(f"Struct '{name}' has {len(struct_data['members'])} members")
        return struct_data

    def _parse_variable(self, var_elem: ET.Element) -> Optional[Dict[str, str]]:
        """Parse a variable/member definition"""
        name = var_elem.get('name')
        var_type = var_elem.get('type')

        if not name or not var_type:
            return None

        # Clean up type name
        var_type = self._clean_type_name(var_type)

        member = {
            'name': name,
            'type': var_type,
            'comment': var_elem.findtext('comment', ''),
            'address': var_elem.get('address', ''),
            'initial_value': var_elem.get('initialValue', '')
        }

        return member

    def _infer_type_from_content(self, name: str, data_type: ET.Element):
        """Try to infer type from element content when baseType is not clear"""
        self._debug(f"Inferring type for '{name}' from content")

        # Check if it has values (likely an enum)
        values = data_type.findall(f'.//{self.namespace}value')
        if values:
            self._debug(f"dataType '{name}' has {len(values)} values, treating as ENUM")
            self.enums[name] = self._parse_enum_from_values(name, data_type)
            return

        # Check if it has variables (likely a structure)
        variables = data_type.findall(f'.//{self.namespace}variable')
        if variables:
            self._debug(f"dataType '{name}' has {len(variables)} variables, treating as STRUCTURE")
            struct_data = {
                'type': 'structure',
                'members': [],
                'comment': '',
                'base_type': ''
            }

            for var_elem in variables:
                member = self._parse_variable(var_elem)
                if member:
                    struct_data['members'].append(member)

            self.structures[name] = struct_data
            return

        self._debug(f"Could not infer type for '{name}'")

    def _parse_pou_elements(self):
        """Parse POU (Program Organization Unit) elements which might contain structures"""
        self._debug("Searching for POU elements")

        pous = self._find_with_namespace('.//pou')
        self._debug(f"Found {len(pous)} POU elements")

        for pou in pous:
            pou_name = pou.get('name', 'UNNAMED_POU')
            pou_type = pou.get('pouType', 'UNKNOWN')
            self._debug(f"POU: '{pou_name}' (type: {pou_type})")

            # Check if this POU contains data types
            interface = pou.find(f'{self.namespace}interface')
            if interface is not None:
                self._parse_pou_interface(pou_name, interface)

    def _parse_pou_interface(self, pou_name: str, interface: ET.Element):
        """Parse a POU interface for local variables that might be structures"""
        self._debug(f"Parsing interface for POU '{pou_name}'")

        local_vars = interface.find(f'{self.namespace}localVars')
        if local_vars is not None:
            variables = local_vars.findall(f'{self.namespace}variable')
            self._debug(f"POU '{pou_name}' has {len(variables)} local variables")

    def _clean_type_name(self, type_name: str) -> str:
        """Clean type names by removing array indicators and whitespace"""
        if not type_name:
            return ''

        # Remove array brackets and dimension
        cleaned = re.sub(r'\[.*?\]', '', type_name)
        # Remove pointer indicators
        cleaned = cleaned.replace('^', '').strip()
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned


# Test function
def test_parser():
    """Test the parser"""
    # Replace with your actual file path
    file_path = "S:/PLC_export_Test/H2N-PLCopen/H2-1.0.02.xml"

    parser = CodesysStructureParser(file_path, debug=True)
    result = parser.parse_all_structures()

    # Save debug log
    parser.save_debug_log('debug_log.txt')

    print(f"\nFinal Results:")
    print(f"Enums: {len(result['enums'])}")
    print(f"Structures: {len(result['structures'])}")
    print(f"Unions: {len(result['unions'])}")

    if result['enums']:
        print("\nFirst few enums:")
        for i, (name, enum_data) in enumerate(list(result['enums'].items())[:3]):
            print(f"  {name}: {len(enum_data['values'])} values")


if __name__ == "__main__":
    test_parser()