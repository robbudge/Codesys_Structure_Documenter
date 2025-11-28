"""
Common XML Parser base class for Codesys PLCopen XML exports
Contains shared processing logic for all XML types
"""

import xml.etree.ElementTree as ET
import logging
import json
from pathlib import Path


class CommonXMLParser:
    """Common base parser with shared processing logic"""

    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        self.logger = logging.getLogger('CodesysXMLDocGenerator.CommonParser')
        self.logger.debug(f"CommonXMLParser initialized with file: {xml_file_path}")

        # Namespace handling
        self.namespaces = {
            'ns': 'http://www.plcopen.org/xml/tc6_0200',
            '': 'http://www.plcopen.org/xml/tc6_0200'
        }

        # Standardized data storage for JSON output
        self.data_types = []
        self.pous = []
        self.global_vars = []
        self.enums = []
        self.unions = []
        self.structures = []

        # Load and parse XML
        self._load_xml()

    def _load_xml(self):
        """Load and parse the XML file"""
        self.logger.debug(f"Loading XML file: {self.xml_file_path}")

        try:
            self.tree = ET.parse(self.xml_file_path)
            self.root = self.tree.getroot()

            # Debug: Log root tag and attributes
            self.logger.debug(f"XML Root: {self.root.tag}, Attributes: {self.root.attrib}")

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

        return []

    def _process_data_type_element(self, data_type_elem):
        """Process individual data type element"""
        try:
            name_elem = self._find_with_fallback(data_type_elem, './name')
            if name_elem is not None and name_elem.text:
                name = name_elem.text

                # Check for duplicates
                if not any(dt['name'] == name for dt in self.data_types):
                    data_type_info = {
                        'name': name,
                        'type': 'dataType',
                        'details': self._extract_data_type_details(data_type_elem)
                    }
                    self.data_types.append(data_type_info)
                    self.logger.debug(f"Added data type: {name}")
            else:
                # Try to get name from attributes
                name = data_type_elem.get('name')
                if name and not any(dt['name'] == name for dt in self.data_types):
                    data_type_info = {
                        'name': name,
                        'type': 'dataType',
                        'details': self._extract_data_type_details(data_type_elem)
                    }
                    self.data_types.append(data_type_info)
                    self.logger.debug(f"Added data type from attribute: {name}")

        except Exception as e:
            self.logger.warning(f"Error processing data type element: {str(e)}")

    def _process_pou_element(self, pou_elem):
        """Process individual POU element with actions and methods"""
        try:
            name_elem = self._find_with_fallback(pou_elem, './name')
            pou_type = pou_elem.get('pouType', 'unknown')

            if name_elem is not None and name_elem.text:
                name = name_elem.text

                # Check for duplicates
                if not any(p['name'] == name for p in self.pous):
                    pou_info = {
                        'name': name,
                        'type': 'pou',
                        'pou_type': pou_type,
                        'details': self._extract_pou_details(pou_elem),
                        'actions': self._extract_actions(pou_elem),
                        'methods': self._extract_methods(pou_elem)
                    }
                    self.pous.append(pou_info)
                    self.logger.debug(
                        f"Added POU: {name} (type: {pou_type}) with {len(pou_info['actions'])} actions, {len(pou_info['methods'])} methods")
            else:
                # Try to get name from attributes
                name = pou_elem.get('name')
                if name and not any(p['name'] == name for p in self.pous):
                    pou_info = {
                        'name': name,
                        'type': 'pou',
                        'pou_type': pou_type,
                        'details': self._extract_pou_details(pou_elem),
                        'actions': self._extract_actions(pou_elem),
                        'methods': self._extract_methods(pou_elem)
                    }
                    self.pous.append(pou_info)
                    self.logger.debug(
                        f"Added POU from attribute: {name} (type: {pou_type}) with {len(pou_info['actions'])} actions, {len(pou_info['methods'])} methods")

        except Exception as e:
            self.logger.warning(f"Error processing POU element: {str(e)}")

    def _extract_actions(self, pou_elem):
        """Extract actions from POU element"""
        actions = []
        try:
            action_elems = self._findall_with_fallback(pou_elem, './/action')
            self.logger.debug(f"Found {len(action_elems)} action elements in POU")

            for action_elem in action_elems:
                action_info = self._extract_action_details(action_elem)
                if action_info:
                    actions.append(action_info)

        except Exception as e:
            self.logger.debug(f"Error extracting actions: {str(e)}")

        return actions

    def _extract_action_details(self, action_elem):
        """Extract details from action element"""
        try:
            name_elem = self._find_with_fallback(action_elem, './name')
            name = name_elem.text if name_elem is not None else action_elem.get('name', 'Unknown Action')

            action_info = {
                'name': name,
                'type': 'action',
                'details': self._extract_pou_details(action_elem)  # Actions have similar structure to POUs
            }

            return action_info

        except Exception as e:
            self.logger.debug(f"Error extracting action details: {str(e)}")
            return None

    def _extract_methods(self, pou_elem):
        """Extract methods from POU element"""
        methods = []
        try:
            method_elems = self._findall_with_fallback(pou_elem, './/method')
            self.logger.debug(f"Found {len(method_elems)} method elements in POU")

            for method_elem in method_elems:
                method_info = self._extract_method_details(method_elem)
                if method_info:
                    methods.append(method_info)

        except Exception as e:
            self.logger.debug(f"Error extracting methods: {str(e)}")

        return methods

    def _extract_method_details(self, method_elem):
        """Extract details from method element"""
        try:
            name_elem = self._find_with_fallback(method_elem, './name')
            name = name_elem.text if name_elem is not None else method_elem.get('name', 'Unknown Method')

            method_info = {
                'name': name,
                'type': 'method',
                'details': self._extract_pou_details(method_elem)  # Methods have similar structure to POUs
            }

            return method_info

        except Exception as e:
            self.logger.debug(f"Error extracting method details: {str(e)}")
            return None

    def _extract_data_type_details(self, data_type_elem):
        """Extract detailed information from data type element"""
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

            # Extract description
            comment_elem = self._find_with_fallback(data_type_elem, './documentation/xhtml/p')
            if comment_elem is not None and comment_elem.text:
                details['description'] = comment_elem.text.strip()

        except Exception as e:
            self.logger.debug(f"Error extracting data type details: {str(e)}")

        return details

    def _extract_pou_details(self, pou_elem):
        """Extract detailed information from POU element"""
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

        except Exception as e:
            self.logger.debug(f"Error extracting POU details: {str(e)}")

        return details

    def _extract_variable_info(self, var_elem):
        """Extract variable information with enhanced type detection and extensive debugging"""
        self.logger.debug("=== EXTRACTING VARIABLE INFO ===")
        self.logger.debug(f"Variable element: {ET.tostring(var_elem, encoding='unicode')[:500]}...")

        try:
            # FIRST: Try to get name from attribute (this is the main issue)
            name_attr = var_elem.get('name')
            self.logger.debug(f"Name attribute: '{name_attr}'")

            # SECOND: Try to get name from child element (fallback)
            name_elem = self._find_with_fallback(var_elem, './name')
            name_from_elem = name_elem.text if name_elem is not None and name_elem.text else None
            self.logger.debug(f"Name element found: {name_elem is not None}, text: '{name_from_elem}'")

            # Use attribute first, then fallback to element
            variable_name = name_attr or name_from_elem
            self.logger.debug(f"Final variable name: '{variable_name}'")

            if not variable_name:
                self.logger.debug("No valid name found for variable")
                return None

            type_elem = self._find_with_fallback(var_elem, './type')
            initial_value_elem = self._find_with_fallback(var_elem, './initialValue')
            comment_elem = self._find_with_fallback(var_elem, './comment')

            # Enhanced type extraction with debugging
            self.logger.debug(f"Type element found: {type_elem is not None}")
            type_info = self._extract_type_info(type_elem)
            self.logger.debug(f"Extracted type info: {type_info}")

            initial_value = ''
            if initial_value_elem is not None:
                self.logger.debug("Initial value element found")
                simple_value_elem = self._find_with_fallback(initial_value_elem, './simpleValue')
                if simple_value_elem is not None and simple_value_elem.text:
                    initial_value = simple_value_elem.text
                    self.logger.debug(f"Initial value: {initial_value}")
            else:
                self.logger.debug("No initial value element found")

            comment = ''
            if comment_elem is not None and comment_elem.text:
                comment = comment_elem.text
                self.logger.debug(f"Comment found: {comment[:100]}...")
            else:
                self.logger.debug("No comment element found")

            var_info = {
                'name': variable_name,  # Use the combined name
                'type': type_info['name'],
                'type_details': type_info,
                'initial_value': initial_value,
                'comment': comment
            }

            self.logger.debug(f"Successfully extracted variable: {var_info['name']} of type {var_info['type']}")
            return var_info

        except Exception as e:
            self.logger.error(f"Error extracting variable info: {str(e)}", exc_info=True)
            return None

    def _extract_type_info(self, type_elem):
        """Extract detailed type information with enhanced debugging"""
        type_info = {
            'name': 'UNKNOWN',
            'category': 'basic',
            'details': {}
        }

        if type_elem is None:
            self.logger.debug("Type element is None, returning UNKNOWN")
            return type_info

        try:
            self.logger.debug(f"=== EXTRACTING TYPE INFO ===")
            self.logger.debug(f"Type element: {ET.tostring(type_elem, encoding='unicode')[:500]}...")

            # Try to get type name
            type_name_elem = self._find_with_fallback(type_elem, './name')
            if type_name_elem is not None and type_name_elem.text:
                type_info['name'] = type_name_elem.text
                self.logger.debug(f"Found type name from name element: {type_info['name']}")
            else:
                self.logger.debug("No type name element found")

            # Check for derived types
            derived_elem = self._find_with_fallback(type_elem, './derived')
            if derived_elem is not None:
                type_info['category'] = 'derived'
                derived_name = derived_elem.get('name')
                if derived_name:
                    type_info['derived_from'] = derived_name
                    type_info['name'] = derived_name  # Use derived name as type name
                self.logger.debug(f"Found derived type: {derived_name}")

            # Check for array types
            array_elem = self._find_with_fallback(type_elem, './array')
            if array_elem is not None:
                type_info['category'] = 'array'
                type_info['dimensions'] = self._extract_array_dimensions(array_elem)
                self.logger.debug(f"Found array type with {len(type_info['dimensions'])} dimensions")

            # Check for pointer types
            pointer_elem = self._find_with_fallback(type_elem, './pointer')
            if pointer_elem is not None:
                type_info['category'] = 'pointer'
                self.logger.debug("Found pointer type")

            # Check for STRING types with length
            string_elem = self._find_with_fallback(type_elem, './string')
            if string_elem is not None:
                type_info['name'] = 'STRING'
                type_info['category'] = 'string'
                length = string_elem.get('length')
                if length:
                    type_info['details']['length'] = length
                self.logger.debug(f"Found string type with length: {length}")

            # Check for WSTRING types with length
            wstring_elem = self._find_with_fallback(type_elem, './WSTRING')
            if wstring_elem is not None:
                type_info['name'] = 'WSTRING'
                type_info['category'] = 'string'
                length = wstring_elem.get('length')
                if length:
                    type_info['details']['length'] = length
                self.logger.debug(f"Found wstring type with length: {length}")

            # Check for basic types
            basic_types = ['BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD', 'SINT', 'USINT', 'INT', 'UINT', 'DINT', 'UDINT',
                           'LINT', 'ULINT', 'REAL', 'LREAL', 'TIME', 'DATE', 'TIME_OF_DAY', 'DATE_AND_TIME']
            for basic_type in basic_types:
                if self._find_with_fallback(type_elem, f'./{basic_type}') is not None:
                    type_info['name'] = basic_type
                    type_info['category'] = 'basic'
                    self.logger.debug(f"Found basic type: {basic_type}")
                    break

            self.logger.debug(f"Final type info: {type_info}")

        except Exception as e:
            self.logger.error(f"Error extracting type info: {str(e)}", exc_info=True)

        return type_info
    def _extract_array_dimensions(self, array_elem):
        """Extract array dimension information"""
        dimensions = []
        try:
            dim_elems = self._findall_with_fallback(array_elem, './dimension')
            for dim_elem in dim_elems:
                lower_bound = dim_elem.get('lower', '0')
                upper_bound = dim_elem.get('upper', '0')
                dimensions.append({
                    'lower': lower_bound,
                    'upper': upper_bound
                })
        except Exception as e:
            self.logger.debug(f"Error extracting array dimensions: {str(e)}")

        return dimensions

    def _extract_global_variables(self):
        """Extract global variables - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _extract_global_variables")

    def _extract_complex_data_types(self):
        """Extract enums, unions, and structures - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _extract_complex_data_types")

    def _get_standardized_json(self):
        """
        Return standardized JSON structure for GUI browsing

        Returns:
            dict: Standardized JSON with DataTypes, POUs, GlobalVars, etc.
        """
        # Calculate summary statistics
        total_actions = sum(len(pou.get('actions', [])) for pou in self.pous)
        total_methods = sum(len(pou.get('methods', [])) for pou in self.pous)

        return {
            "source_file": Path(self.xml_file_path).name,
            "export_type": self.export_type,
            "DataTypes": self.data_types,
            "POUs": self.pous,
            "GlobalVariables": self.global_vars,
            "Enums": self.enums,
            "Unions": self.unions,
            "Structures": self.structures,
            "summary": {
                "data_types_count": len(self.data_types),
                "pous_count": len(self.pous),
                "global_vars_count": len(self.global_vars),
                "enums_count": len(self.enums),
                "unions_count": len(self.unions),
                "structures_count": len(self.structures),
                "actions_count": total_actions,
                "methods_count": total_methods,
                "total_items": (len(self.data_types) + len(self.pous) + len(self.global_vars) +
                                len(self.enums) + len(self.unions) + len(self.structures) +
                                total_actions + total_methods)
            }
        }

    # Complex data type methods (shared across all parsers)

    def _process_complex_data_type(self, data_type_elem):
        """Process a data type element and classify it with union detection"""
        try:
            name = data_type_elem.get('name')
            if not name:
                name_elem = self._find_with_fallback(data_type_elem, './name')
                if name_elem is not None and name_elem.text:
                    name = name_elem.text

            if not name:
                self.logger.debug("Skipping dataType without name")
                return

            self.logger.debug(f"Processing complex data type: {name}")

            # Check if it's a union FIRST (since unions can be in different locations)
            if self._is_union(data_type_elem):
                self.logger.debug(f"  - Classified as UNION: {name}")
                if not any(u['name'] == name for u in self.unions):
                    union_info = {
                        'name': name,
                        'type': 'union',
                        'members': self._extract_union_members(data_type_elem),
                        'details': self._extract_data_type_details(data_type_elem)
                    }
                    self.unions.append(union_info)
                    self.logger.debug(f"  - Added union: {name} with {len(union_info['members'])} members")
                return

            # Check if it's an enum
            if self._is_enum(data_type_elem):
                self.logger.debug(f"  - Classified as ENUM: {name}")
                if not any(e['name'] == name for e in self.enums):
                    enum_info = {
                        'name': name,
                        'type': 'enum',
                        'values': self._extract_enum_values(data_type_elem),
                        'base_type': self._extract_enum_base_type(data_type_elem),
                        'details': self._extract_data_type_details(data_type_elem)
                    }
                    self.enums.append(enum_info)
                    self.logger.debug(f"  - Added enum: {name} with {len(enum_info['values'])} values")
                return

            # Check if it's a structure
            if self._is_structure(data_type_elem):
                self.logger.debug(f"  - Classified as STRUCTURE: {name}")
                if not any(s['name'] == name for s in self.structures):
                    struct_info = {
                        'name': name,
                        'type': 'structure',
                        'members': self._extract_structure_members(data_type_elem),
                        'details': self._extract_data_type_details(data_type_elem)
                    }
                    self.structures.append(struct_info)
                    self.logger.debug(f"  - Added structure: {name} with {len(struct_info['members'])} members")
                return

            # If none of the above, treat as basic data type
            self.logger.debug(f"  - Classified as BASIC DATATYPE: {name}")
            if not any(dt['name'] == name for dt in self.data_types):
                data_type_info = {
                    'name': name,
                    'type': 'dataType',
                    'details': self._extract_data_type_details(data_type_elem)
                }
                self.data_types.append(data_type_info)
                self.logger.debug(f"  - Added basic data type: {name}")

        except Exception as e:
            self.logger.warning(f"Error processing complex data type: {str(e)}")

    def _is_union(self, data_type_elem):
        """Check if data type is a union - enhanced detection"""
        # Check if it's directly a union element
        if data_type_elem.tag.endswith('union'):
            return True

        # Check if it's in union-specific addData
        parent = data_type_elem.getparent()
        if parent is not None:
            grandparent = parent.getparent()
            if (grandparent is not None and
                grandparent.tag.endswith('data') and
                'union' in grandparent.get('name', '').lower()):
                return True

        # Check for union structure pattern
        members = self._findall_with_fallback(data_type_elem, './/variable')
        return len(members) > 1 and 'union' in data_type_elem.get('name', '').lower()

    def _extract_union_members(self, union_elem):
        """Extract union members with enhanced detection"""
        members = []
        try:
            # If this is a direct union element
            if union_elem.tag.endswith('union'):
                member_elems = self._findall_with_fallback(union_elem, './/variable')
                for member_elem in member_elems:
                    member_info = self._extract_variable_info(member_elem)
                    if member_info:
                        members.append(member_info)
            else:
                # If this is a dataType element containing a union
                union_elem_direct = self._find_with_fallback(union_elem, './/union')
                if union_elem_direct is not None:
                    member_elems = self._findall_with_fallback(union_elem_direct, './/variable')
                    for member_elem in member_elems:
                        member_info = self._extract_variable_info(member_elem)
                        if member_info:
                            members.append(member_info)

        except Exception as e:
            self.logger.debug(f"Error extracting union members: {str(e)}")

        return members

    def _is_union(self, data_type_elem):
        """Check if data type is a union - enhanced detection"""
        # Check if it's directly a union element
        if data_type_elem.tag.endswith('union'):
            return True

        # Check if it's in union-specific addData (without using getparent)
        # Look for union elements in the current element first
        if self._find_with_fallback(data_type_elem, './/union') is not None:
            return True

        # Check for union structure pattern
        members = self._findall_with_fallback(data_type_elem, './/variable')
        return len(members) > 1 and 'union' in data_type_elem.get('name', '').lower()
    def _extract_enum_values(self, enum_elem):
        """Extract enum values with enhanced detection"""
        values = []
        try:
            # Try different patterns for enum values
            value_elems = self._findall_with_fallback(enum_elem, './/values//value')
            if not value_elems:
                value_elems = self._findall_with_fallback(enum_elem, './/enumValue')
            if not value_elems:
                # Look in baseType
                base_type_elem = self._find_with_fallback(enum_elem, './baseType')
                if base_type_elem is not None:
                    value_elems = self._findall_with_fallback(base_type_elem, './/values//value')
                    if not value_elems:
                        value_elems = self._findall_with_fallback(base_type_elem, './/enumValue')

            self.logger.debug(f"Found {len(value_elems)} enum value elements")

            for value_elem in value_elems:
                value_name = value_elem.get('name')
                if not value_name:
                    name_elem = self._find_with_fallback(value_elem, './name')
                    if name_elem is not None and name_elem.text:
                        value_name = name_elem.text

                value_info = {
                    'name': value_name or f'Value_{len(values)}',
                    'value': value_elem.get('value', ''),
                    'details': self._extract_data_type_details(value_elem)
                }
                values.append(value_info)
                self.logger.debug(f"  - Enum value: {value_info['name']} = {value_info['value']}")

        except Exception as e:
            self.logger.debug(f"Error extracting enum values: {str(e)}")

        return values

    def _extract_enum_base_type(self, enum_elem):
        """Extract base type of enum"""
        try:
            base_type_elem = self._find_with_fallback(enum_elem, './baseType')
            if base_type_elem is not None:
                # Check if baseType has a name
                base_type_name = self._find_with_fallback(base_type_elem, './name')
                if base_type_name is not None and base_type_name.text:
                    return base_type_name.text

                # Check if it's an enum base type
                if self._find_with_fallback(base_type_elem, './enum') is not None:
                    return 'ENUM'

                # Check for specific types
                basic_types = ['INT', 'DINT', 'SINT', 'USINT', 'UINT', 'UDINT', 'BYTE', 'WORD', 'DWORD']
                for basic_type in basic_types:
                    if self._find_with_fallback(base_type_elem, f'./{basic_type}') is not None:
                        return basic_type
        except Exception as e:
            self.logger.debug(f"Error extracting enum base type: {str(e)}")

        return 'INT'  # Default base type for enums

    def _is_structure(self, data_type_elem):
        """Check if data type is a structure"""
        # Structures have members and are not enums or unions
        members = self._findall_with_fallback(data_type_elem, './/variable')
        return len(members) > 0 and not self._is_enum(data_type_elem) and not self._is_union(data_type_elem)

    def _extract_structure_members(self, struct_elem):
        """Extract structure members"""
        members = []
        try:
            member_elems = self._findall_with_fallback(struct_elem, './/variable')
            for member_elem in member_elems:
                member_info = self._extract_variable_info(member_elem)
                if member_info:
                    members.append(member_info)

        except Exception as e:
            self.logger.debug(f"Error extracting structure members: {str(e)}")

        return members


if __name__ == "__main__":
    print("This module is intended to be used as a base class")