"""
XML Parser for Codesys PLCopen XML exports
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
from lxml import etree

from data_models import *

class CodesysXmlParser:
    """Parser for Codesys XML exports"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        # Common PLCopen namespaces
        self.namespaces = {
            'xhtml': 'http://www.w3.org/1999/xhtml',
            'plc': 'http://www.plcopen.org/xml/tc6_0200',  # Based on debug findings
            'plc2': 'http://www.plcopen.org/xml/tc6_0201',
            'plc3': 'http://www.plcopen.org/xml/tc6_0100',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        # Primary namespace URI based on debug findings
        self.primary_namespace = 'http://www.plcopen.org/xml/tc6_0200'

    def parse_file(self, file_path: str) -> XmlExport:
        """Parse XML file and return structured data"""
        self.logger.info(f"Parsing XML file: {file_path}")

        # Detect export type
        export_type = self._detect_export_type(file_path)
        self.logger.debug(f"Detected export type: {export_type}")

        # Create export structure
        xml_export = XmlExport(
            export_type=export_type,
            file_path=file_path
        )

        try:
            # Parse with lxml for namespace support
            tree = etree.parse(file_path)
            root = tree.getroot()

            # Log root element for debugging
            self.logger.debug(f"Root element: {etree.QName(root.tag).localname}")
            self.logger.debug(f"Root attributes: {dict(root.attrib)}")

            # Register all namespaces found in the document
            self._register_all_namespaces(root)

            # Parse based on export type
            if export_type == XmlExportType.TYPE_B:
                self.logger.debug("Parsing as Type B export")
                self._parse_type_b(root, xml_export)
            elif export_type == XmlExportType.PROJECT:
                self.logger.debug("Parsing as Project export")
                self._parse_project(root, xml_export)
            elif export_type == XmlExportType.LIBRARY:
                self.logger.debug("Parsing as Library export")
                self._parse_library(root, xml_export)
            elif export_type == XmlExportType.APPLICATION:
                self.logger.debug("Parsing as Application export")
                self._parse_application(root, xml_export)
            else:
                self.logger.warning(f"Unknown export type: {export_type}, attempting generic parse")
                self._parse_generic(root, xml_export)

            self.logger.info(f"Parsed {xml_export.get_summary()['total_items']} items")
            return xml_export

        except Exception as e:
            self.logger.error(f"Error parsing XML: {str(e)}", exc_info=True)
            raise

    def _register_all_namespaces(self, root):
        """Register all namespaces found in the XML"""
        nsmap = root.nsmap
        self.logger.debug(f"Document namespaces: {nsmap}")

        # Update primary namespace if found in document
        for prefix, uri in nsmap.items():
            if 'plcopen' in uri.lower():
                self.primary_namespace = uri
                self.logger.debug(f"Set primary namespace to: {uri}")
                break

    def _detect_export_type(self, file_path: str) -> XmlExportType:
        """Detect the type of XML export"""
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()

            # Check root element
            root_tag = etree.QName(root.tag).localname
            self.logger.debug(f"Root tag: {root_tag}")

            if root_tag == 'project':
                return XmlExportType.PROJECT
            elif root_tag == 'library':
                return XmlExportType.LIBRARY
            elif root_tag == 'application':
                return XmlExportType.APPLICATION

            # Check for Type B specific elements
            for elem in root.iter():
                tag_name = etree.QName(elem.tag).localname
                if 'resource' in tag_name.lower():
                    self.logger.debug(f"Found resource element: {tag_name}")
                    return XmlExportType.TYPE_B

            return XmlExportType.UNKNOWN

        except Exception as e:
            self.logger.error(f"Error detecting export type: {str(e)}")
            return XmlExportType.UNKNOWN

    def _parse_generic(self, root, xml_export: XmlExport):
        """Generic parsing that works for most export types - UPDATED"""
        self.logger.debug("Starting generic parse")

        # Use the primary namespace URI directly with braces
        namespace = '{' + self.primary_namespace + '}'

        # Find all dataType elements
        data_types = root.findall(f'.//{namespace}dataType')
        self.logger.debug(f"Found {len(data_types)} dataType elements")

        # Track what we find
        enum_count = 0
        struct_count = 0
        union_count = 0
        basic_count = 0

        for data_type_elem in data_types:
            name = data_type_elem.get('name', 'Unknown')

            # Check what type of dataType this is
            has_union = data_type_elem.find(f'{namespace}union') is not None
            has_struct = data_type_elem.find(f'{namespace}struct') is not None
            has_values = len(data_type_elem.findall(f'.//{namespace}value')) > 0

            if has_union:
                self.logger.debug(f"DataType '{name}' CONTAINS UNION")
                union_count += 1
            elif has_struct:
                self.logger.debug(f"DataType '{name}' CONTAINS STRUCT")
                struct_count += 1
            elif has_values:
                self.logger.debug(f"DataType '{name}' CONTAINS VALUES (ENUM)")
                enum_count += 1
            else:
                self.logger.debug(f"DataType '{name}' is BASIC TYPE")
                basic_count += 1

            # Parse it
            self._parse_data_type_comprehensive(data_type_elem, xml_export, namespace)

        # NEW: Look for STANDALONE struct and union elements (not inside dataType)
        self.logger.debug(f"\n=== LOOKING FOR STANDALONE STRUCTURES ===")

        # Find all struct elements that are NOT inside a dataType
        all_structs = root.findall(f'.//{namespace}struct')
        standalone_structs = []
        for struct_elem in all_structs:
            parent = struct_elem.getparent()
            if parent is not None:
                parent_tag = etree.QName(parent.tag).localname
                if parent_tag != 'dataType':
                    standalone_structs.append(struct_elem)

        self.logger.debug(f"Found {len(standalone_structs)} standalone struct elements")

        # Find all union elements that are NOT inside a dataType
        all_unions = root.findall(f'.//{namespace}union')
        standalone_unions = []
        for union_elem in all_unions:
            parent = union_elem.getparent()
            if parent is not None:
                parent_tag = etree.QName(parent.tag).localname
                if parent_tag != 'dataType':
                    standalone_unions.append(union_elem)

        self.logger.debug(f"Found {len(standalone_unions)} standalone union elements")

        # Parse standalone structs
        for struct_elem in standalone_structs:
            self._parse_standalone_structure(struct_elem, xml_export, namespace)

        # Parse standalone unions
        for union_elem in standalone_unions:
            self._parse_standalone_union(union_elem, xml_export, namespace)

        self.logger.debug(f"\n=== SUMMARY ===")
        self.logger.debug(f"Unions detected in dataTypes: {union_count}")
        self.logger.debug(f"Structs detected in dataTypes: {struct_count}")
        self.logger.debug(f"Enums detected: {enum_count}")
        self.logger.debug(f"Basic types: {basic_count}")
        self.logger.debug(f"Standalone unions: {len(standalone_unions)}")
        self.logger.debug(f"Standalone structs: {len(standalone_structs)}")
        self.logger.debug(f"=== END SUMMARY ===\n")

        # Find all POU elements
        pous = root.findall(f'.//{namespace}pou')
        self.logger.debug(f"Found {len(pous)} pou elements")

        for pou_elem in pous:
            self._parse_pou_direct(pou_elem, xml_export, namespace)

        # Find all globalVars elements
        global_vars = root.findall(f'.//{namespace}globalVars')
        self.logger.debug(f"Found {len(global_vars)} globalVars elements")

        for global_var_elem in global_vars:
            self._parse_global_vars_direct(global_var_elem, xml_export, namespace)

    def _parse_data_type_comprehensive(self, elem, xml_export: XmlExport, namespace):
        """Comprehensive data type parsing - FIXED VERSION"""
        name = elem.get('name', '')
        self.logger.debug(f"Parsing data type: {name}")

        if not name:
            return

        # DEBUG: Show all children of this dataType
        children = list(elem)
        child_tags = [etree.QName(child.tag).localname for child in children]
        self.logger.debug(f"  Children tags: {child_tags}")

        # Check each child to see what we have
        for child in children:
            child_tag = etree.QName(child.tag).localname

            # 1. Check for union element
            if child_tag == 'union':
                self.logger.debug(f"  -> FOUND UNION CHILD for {name}")
                self._parse_union_comprehensive(elem, xml_export, namespace)
                return

            # 2. Check for struct element
            if child_tag == 'struct':
                self.logger.debug(f"  -> FOUND STRUCT CHILD for {name}")
                self._parse_structure_comprehensive(elem, xml_export, namespace)
                return

        # 3. Check for baseType element that contains struct
        base_type_elem = elem.find(f'{namespace}baseType')
        if base_type_elem is not None:
            # Check if baseType contains struct
            struct_elem = base_type_elem.find(f'{namespace}struct')
            if struct_elem is not None:
                self.logger.debug(f"  -> FOUND STRUCT INSIDE baseType for {name}")
                self._parse_structure_comprehensive(elem, xml_export, namespace)
                return

            # Check if baseType contains union
            union_elem = base_type_elem.find(f'{namespace}union')
            if union_elem is not None:
                self.logger.debug(f"  -> FOUND UNION INSIDE baseType for {name}")
                self._parse_union_comprehensive(elem, xml_export, namespace)
                return

            # Check for enum values
            value_elements = []

            # Direct value elements under baseType
            value_elements = base_type_elem.findall(f'{namespace}value')

            # Check for values element
            if not value_elements:
                values_elem = base_type_elem.find(f'{namespace}values')
                if values_elem is not None:
                    value_elements = values_elem.findall(f'{namespace}value')

            if value_elements:
                self.logger.debug(f"  Found {len(value_elements)} value elements for {name} - treating as enum")
                self._parse_enum_comprehensive(elem, xml_export, namespace, value_elements)
                return

        # 4. Check for value elements anywhere
        value_elements = elem.findall(f'.//{namespace}value')
        if value_elements:
            self.logger.debug(f"  Found {len(value_elements)} value elements anywhere for {name} - treating as enum")
            self._parse_enum_comprehensive(elem, xml_export, namespace, value_elements)
            return

        # 5. Default: regular data type
        self._add_basic_data_type(elem, xml_export, namespace)

    def _add_basic_data_type(self, elem, xml_export: XmlExport, namespace):
        """Add a basic data type"""
        name = elem.get('name', '')
        base_type = elem.get('baseType', 'UNKNOWN')
        initial_value = None

        # Check for baseType element if attribute is not set
        if base_type == 'UNKNOWN':
            base_type_elem = elem.find(f'{namespace}baseType')
            if base_type_elem is not None:
                base_type = base_type_elem.get('name', 'UNKNOWN')

        init_value_elem = elem.find(f'{namespace}initialValue')
        if init_value_elem is not None:
            initial_value = init_value_elem.text

        data_type = DataType(
            name=name,
            base_type=base_type,
            initial_value=initial_value
        )

        xml_export.data_types.append(data_type)
        self.logger.debug(f"Added basic data type: {name} ({base_type})")





    def _parse_enum_comprehensive(self, elem, xml_export: XmlExport, namespace, value_elements=None):
        """Parse enumeration comprehensively"""
        name = elem.get('name', '')
        self.logger.debug(f"==== PARSING ENUM: {name} ====")

        base_type = 'INT'

        # Get base type from baseType child element
        base_type_elem = elem.find(f'{namespace}baseType')
        if base_type_elem is not None:
            base_type_name = base_type_elem.get('name', 'INT')
            base_type = base_type_name
            self.logger.debug(f"  Base type from baseType element: {base_type}")

        # Parse enum values
        values = []

        if value_elements is None:
            value_elements = elem.findall(f'.//{namespace}value')

        self.logger.debug(f"  Processing {len(value_elements)} enum values")

        # Track used values to auto-assign sequential values
        used_values = set()
        auto_value = 0

        for i, value_elem in enumerate(value_elements):
            value_name = value_elem.get('name', f'Value_{i}')
            value_value = value_elem.get('value', '')

            # Handle values without value attribute (use text content or auto-assign)
            if not value_value or value_value == 'None':
                if value_elem.text and value_elem.text.strip():
                    value_value = value_elem.text.strip()
                else:
                    # Auto-assign sequential value
                    while str(auto_value) in used_values:
                        auto_value += 1
                    value_value = str(auto_value)
                    auto_value += 1

            # Clean up the value
            if value_value == 'None' or not value_value:
                value_value = str(auto_value)
                auto_value += 1

            value_desc = value_elem.get('description', '')

            # Store used value
            used_values.add(value_value)

            enum_value = EnumValue(
                name=value_name,
                value=value_value,
                description=value_desc if value_desc else None
            )
            values.append(enum_value)
            self.logger.debug(f"    Enum value {i}: {value_name} = {value_value}")

        enum_type = EnumType(
            name=name,
            base_type=base_type,
            values=values
        )

        xml_export.enums.append(enum_type)
        self.logger.debug(f"SUCCESS: Added enum: {name} with {len(values)} values (base type: {base_type})")
        self.logger.debug(f"==== END ENUM: {name} ====\n")

    def _parse_pou_direct(self, elem, xml_export: XmlExport, namespace):
        """Parse POU directly using namespace"""
        name = elem.get('name', '')
        self.logger.debug(f"Parsing POU: {name}")

        pou_type_str = elem.get('pouType', 'functionBlock').lower()

        # Map string to PouType enum
        pou_type_map = {
            'function': PouType.FUNCTION,
            'functionblock': PouType.FUNCTION_BLOCK,
            'program': PouType.PROGRAM
        }
        pou_type = pou_type_map.get(pou_type_str, PouType.FUNCTION_BLOCK)

        # Parse return type
        return_type = 'VOID'

        interface_elem = elem.find(f'{namespace}interface')
        if interface_elem is not None:
            return_type_elem = interface_elem.find(f'{namespace}returnType')
            if return_type_elem is not None:
                return_type = return_type_elem.get('type', 'VOID')

        # Parse variables
        variables = []

        # Look for variables in interface
        if interface_elem is not None:
            var_elements = interface_elem.findall(f'{namespace}variable')
            self.logger.debug(f"Found {len(var_elements)} variables for POU {name}")

            for var_elem in var_elements:
                var_name = var_elem.get('name', '')
                var_type = var_elem.get('type', '')
                var_init = None

                init_elem = var_elem.find(f'{namespace}initialValue')
                if init_elem is not None:
                    var_init = init_elem.text

                if var_name and var_type:
                    variable = Variable(
                        name=var_name,
                        type=var_type,
                        initial_value=var_init
                    )
                    variables.append(variable)
                    self.logger.debug(f"  Variable: {var_name} : {var_type}")

        # Parse implementation
        implementation = None

        body_elem = elem.find(f'{namespace}body')
        if body_elem is not None:
            st_elem = body_elem.find(f'{namespace}ST')
            if st_elem is not None and st_elem.text:
                implementation = st_elem.text.strip()
                self.logger.debug(f"Found implementation for POU {name}")

        pou = Pou(
            name=name,
            pou_type=pou_type,
            return_type=return_type,
            variables=variables,
            implementation=implementation
        )

        xml_export.pous.append(pou)
        self.logger.debug(f"Added POU: {name} ({pou_type.value}) with {len(variables)} variables")

    def _parse_global_vars_direct(self, elem, xml_export: XmlExport, namespace):
        """Parse global variables directly using namespace"""
        self.logger.debug("Parsing global variables")

        var_elements = elem.findall(f'{namespace}variable')
        self.logger.debug(f"Found {len(var_elements)} global variables")

        for var_elem in var_elements:
            var_name = var_elem.get('name', '')
            var_type = var_elem.get('type', '')
            var_init = None

            init_elem = var_elem.find(f'{namespace}initialValue')
            if init_elem is not None:
                var_init = init_elem.text

            if var_name and var_type:
                global_var = GlobalVariable(
                    name=var_name,
                    type=var_type,
                    initial_value=var_init
                )
                xml_export.global_variables.append(global_var)
                self.logger.debug(f"  Global variable: {var_name} : {var_type}")

    def _parse_type_b(self, root, xml_export: XmlExport):
        """Parse Type B (Resource) export"""
        self.logger.debug("Parsing Type B export")
        self._parse_generic(root, xml_export)

    def _parse_project(self, root, xml_export: XmlExport):
        """Parse Project export"""
        self.logger.debug("Parsing Project export")
        self._parse_generic(root, xml_export)

    def _parse_library(self, root, xml_export: XmlExport):
        """Parse Library export"""
        self.logger.debug("Parsing Library export")
        self._parse_generic(root, xml_export)

    def _parse_application(self, root, xml_export: XmlExport):
        """Parse Application export"""
        self.logger.debug("Parsing Application export")
        self._parse_generic(root, xml_export)

    def _parse_standalone_structure(self, struct_elem, xml_export: XmlExport, namespace):
        """Parse a standalone struct element (not inside dataType) - FIXED VERSION"""
        self.logger.debug(f"==== PARSING STANDALONE STRUCT ====")

        # Get the parent element to get the correct name
        parent_elem = struct_elem.getparent()
        if parent_elem is None:
            self.logger.debug(f"No parent found for standalone struct")
            name = struct_elem.get('name', 'Standalone_Struct')
        else:
            # Get name from the parent element (likely a dataType or similar)
            parent_name = parent_elem.get('name', '')
            if parent_name:
                name = parent_name
                self.logger.debug(f"Using parent name for structure: {name}")
            else:
                # Fallback to struct element's own name
                name = struct_elem.get('name', 'Standalone_Struct')

        self.logger.debug(f"Parsing standalone structure: {name}")

        members = []

        # Get ALL variable elements from the struct (at any depth)
        member_elements = struct_elem.findall(f'.//{namespace}variable')
        self.logger.debug(f"  Found {len(member_elements)} variable elements in struct")

        for i, member_elem in enumerate(member_elements):
            member_name = member_elem.get('name', f'Member_{i}')
            member_type = ''
            member_init = None

            # Get type from child <type> element
            type_elem = member_elem.find(f'{namespace}type')
            if type_elem is not None:
                # Check for direct type elements like <INT />
                for child in type_elem:
                    child_tag = etree.QName(child.tag).localname
                    if child_tag in ['INT', 'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD', 'SINT', 'USINT', 'UINT', 'UDINT',
                                     'ULINT', 'REAL', 'LREAL', 'TIME', 'DATE', 'TOD', 'DT', 'STRING', 'WSTRING']:
                        member_type = child_tag
                        break
                    elif child_tag == 'derived':
                        member_type = child.get('name', '')
                        break

            # OLD way (backward compatibility): Check type attribute
            if not member_type:
                member_type = member_elem.get('type', '')

            # Also check for baseType if type attribute is empty
            if not member_type:
                base_type_elem = member_elem.find(f'{namespace}baseType')
                if base_type_elem is not None:
                    member_type = base_type_elem.get('name', '')

            init_elem = member_elem.find(f'{namespace}initialValue')
            if init_elem is not None:
                member_init = init_elem.text

            if member_name and member_type:
                member = StructureMember(
                    name=member_name,
                    type=member_type,
                    initial_value=member_init
                )
                members.append(member)
                self.logger.debug(f"    Member {i}: {member_name} : {member_type}")
            else:
                self.logger.debug(f"    Skipping member {i} - name: '{member_name}', type: '{member_type}'")
                # DEBUG: Show what's in the variable element
                children = list(member_elem)
                child_tags = [etree.QName(child.tag).localname for child in children]
                self.logger.debug(f"      Variable children: {child_tags}")

        if members:
            structure = StructureType(
                name=name,
                members=members
            )
            xml_export.structures.append(structure)
            self.logger.debug(f"SUCCESS: Added standalone structure: {name} with {len(members)} members")
            self.logger.debug(f"==== END STANDALONE STRUCT: {name} ====\n")
        else:
            self.logger.debug(f"FAILED: No valid members found for standalone structure: {name}")
            self.logger.debug(f"==== END STANDALONE STRUCT (FAILED): {name} ====\n")

    def _parse_union_comprehensive(self, elem, xml_export: XmlExport, namespace):
        """Parse union comprehensively - UPDATED"""
        name = elem.get('name', '')
        self.logger.debug(f"==== PARSING UNION: {name} ====")

        members = []

        # Find union element
        union_elem = elem.find(f'{namespace}union')
        if union_elem is None:
            return

        # Get ALL variable elements from the union (at any depth)
        member_elements = union_elem.findall(f'.//{namespace}variable')
        self.logger.debug(f"  Found {len(member_elements)} variable elements in union")

        for i, member_elem in enumerate(member_elements):
            member_name = member_elem.get('name', f'Member_{i}')
            member_type = ''
            member_init = None

            # NEW: Get type from child <type> element
            type_elem = member_elem.find(f'{namespace}type')
            if type_elem is not None:
                # Check for direct type elements
                for child in type_elem:
                    child_tag = etree.QName(child.tag).localname
                    if child_tag in ['INT', 'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD', 'SINT', 'USINT', 'UINT', 'UDINT',
                                     'ULINT', 'REAL', 'LREAL', 'TIME', 'DATE', 'TOD', 'DT', 'STRING', 'WSTRING']:
                        member_type = child_tag
                        break
                    elif child_tag == 'derived':
                        member_type = child.get('name', '')
                        break

            # OLD way (backward compatibility)
            if not member_type:
                member_type = member_elem.get('type', '')

            if not member_type:
                base_type_elem = member_elem.find(f'{namespace}baseType')
                if base_type_elem is not None:
                    member_type = base_type_elem.get('name', '')

            init_elem = member_elem.find(f'{namespace}initialValue')
            if init_elem is not None:
                member_init = init_elem.text

            if member_name and member_type:
                member = StructureMember(
                    name=member_name,
                    type=member_type,
                    initial_value=member_init
                )
                members.append(member)
                self.logger.debug(f"    Member {i}: {member_name} : {member_type}")

        if members:
            union = StructureType(
                name=name,
                members=members
            )
            xml_export.unions.append(union)
            self.logger.debug(f"SUCCESS: Added union: {name} with {len(members)} members")
        else:
            self.logger.debug(f"FAILED: No valid members found for union: {name}")

    def _parse_structure_comprehensive(self, elem, xml_export: XmlExport, namespace):
        """Parse structure comprehensively - UPDATED"""
        name = elem.get('name', '')
        self.logger.debug(f"==== PARSING STRUCTURE: {name} ====")

        members = []

        # FIRST: Try to find struct directly in dataType
        struct_elem = elem.find(f'{namespace}struct')

        # SECOND: If not found, try to find struct inside baseType
        if struct_elem is None:
            base_type_elem = elem.find(f'{namespace}baseType')
            if base_type_elem is not None:
                struct_elem = base_type_elem.find(f'{namespace}struct')

        if struct_elem is None:
            self.logger.debug(f"No struct element found for {name}")
            return

        # Get ALL variable elements from the struct (at any depth)
        member_elements = struct_elem.findall(f'.//{namespace}variable')
        self.logger.debug(f"  Found {len(member_elements)} variable elements in struct")

        for i, member_elem in enumerate(member_elements):
            member_name = member_elem.get('name', f'Member_{i}')
            member_type = ''
            member_init = None

            # Get type from child <type> element
            type_elem = member_elem.find(f'{namespace}type')
            if type_elem is not None:
                # Check for direct type elements like <INT />, <BOOL />, etc.
                for child in type_elem:
                    child_tag = etree.QName(child.tag).localname
                    if child_tag in ['INT', 'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD', 'SINT', 'USINT', 'UINT', 'UDINT',
                                     'ULINT', 'REAL', 'LREAL', 'TIME', 'DATE', 'TOD', 'DT', 'STRING', 'WSTRING']:
                        member_type = child_tag
                        break
                    elif child_tag == 'derived':
                        member_type = child.get('name', '')
                        break
                    elif child_tag == 'string':
                        # Handle string type with length attribute
                        length = child.get('length', '80')
                        member_type = f'STRING({length})'
                        break
                    elif child_tag == 'wstring':
                        # Handle wstring type with length attribute
                        length = child.get('length', '80')
                        member_type = f'WSTRING({length})'
                        break

            # OLD way (backward compatibility)
            if not member_type:
                member_type = member_elem.get('type', '')

            if not member_type:
                base_type_elem = member_elem.find(f'{namespace}baseType')
                if base_type_elem is not None:
                    member_type = base_type_elem.get('name', '')

            init_elem = member_elem.find(f'{namespace}initialValue')
            if init_elem is not None:
                member_init = init_elem.text

            if member_name and member_type:
                member = StructureMember(
                    name=member_name,
                    type=member_type,
                    initial_value=member_init
                )
                members.append(member)
                self.logger.debug(f"    Member {i}: {member_name} : {member_type}")
            else:
                self.logger.debug(f"    Skipping member {i} - name: '{member_name}', type: '{member_type}'")

        if members:
            structure = StructureType(
                name=name,
                members=members
            )
            xml_export.structures.append(structure)
            self.logger.debug(f"SUCCESS: Added structure: {name} with {len(members)} members")
            self.logger.debug(f"==== END STRUCTURE: {name} ====\n")
        else:
            self.logger.debug(f"FAILED: No valid members found for structure: {name}")
            self.logger.debug(f"==== END STRUCTURE (FAILED): {name} ====\n")

    def _parse_standalone_union(self, union_elem, xml_export: XmlExport, namespace):
        """Parse a standalone union element (not inside dataType)"""
        self.logger.debug(f"==== PARSING STANDALONE UNION ====")

        # Get name from the union element
        name = union_elem.get('name', 'Standalone_Union')

        self.logger.debug(f"Parsing standalone union: {name}")

        members = []

        # Get ALL variable elements from the union (at any depth)
        member_elements = union_elem.findall(f'.//{namespace}variable')
        self.logger.debug(f"  Found {len(member_elements)} variable elements in union")

        for i, member_elem in enumerate(member_elements):
            member_name = member_elem.get('name', f'Member_{i}')
            member_type = ''
            member_init = None

            # Get type from child <type> element
            type_elem = member_elem.find(f'{namespace}type')
            if type_elem is not None:
                # Check for direct type elements
                for child in type_elem:
                    child_tag = etree.QName(child.tag).localname
                    if child_tag in ['INT', 'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD', 'SINT', 'USINT', 'UINT', 'UDINT',
                                     'ULINT', 'REAL', 'LREAL', 'TIME', 'DATE', 'TOD', 'DT', 'STRING', 'WSTRING']:
                        member_type = child_tag
                        break
                    elif child_tag == 'derived':
                        member_type = child.get('name', '')
                        break

            # OLD way (backward compatibility)
            if not member_type:
                member_type = member_elem.get('type', '')

            if not member_type:
                base_type_elem = member_elem.find(f'{namespace}baseType')
                if base_type_elem is not None:
                    member_type = base_type_elem.get('name', '')

            init_elem = member_elem.find(f'{namespace}initialValue')
            if init_elem is not None:
                member_init = init_elem.text

            if member_name and member_type:
                member = StructureMember(
                    name=member_name,
                    type=member_type,
                    initial_value=member_init
                )
                members.append(member)
                self.logger.debug(f"    Member {i}: {member_name} : {member_type}")

        if members:
            union = StructureType(
                name=name,
                members=members,
                is_union=True  # NEW: Mark as union
            )
            xml_export.unions.append(union)
            self.logger.debug(f"SUCCESS: Added standalone union: {name} with {len(members)} members")
            self.logger.debug(f"==== END STANDALONE UNION: {name} ====\n")
        else:
            self.logger.debug(f"FAILED: No valid members found for standalone union: {name}")
            self.logger.debug(f"==== END STANDALONE UNION (FAILED): {name} ====\n")

    # Update _parse_structure_comprehensive similarly with is_union=False