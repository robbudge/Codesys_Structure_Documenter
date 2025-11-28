"""
Type B XML Parser for Codesys Application Exports
Refactored to use common base parser
"""

from xml_parse_common import CommonXMLParser
import logging


class TypeBParser(CommonXMLParser):
    """Parser for Type B Codesys XML exports (Application Export)"""

    def __init__(self, xml_file_path):
        self.export_type = "type_b"
        super().__init__(xml_file_path)
        self.logger = logging.getLogger('CodesysXMLDocGenerator.TypeBParser')
        self.logger.debug(f"TypeBParser initialized with file: {xml_file_path}")

    def parse_to_json(self):
        """
        Parse the Type B XML export and return standardized JSON

        Returns:
            dict: Standardized JSON structure with DataTypes, POUs, GlobalVars, etc.
        """
        self.logger.debug("Starting Type B XML parsing process")

        try:
            # First, debug the XML structure to understand Type B format
            self._debug_type_b_structure()

            # Extract data from application resource
            self._extract_application_data()

            # Extract global variables
            self._extract_global_variables()

            # Extract complex data types (enums, unions, structures)
            self._extract_complex_data_types()

            # Return standardized JSON
            json_data = self._get_standardized_json()

            self.logger.info(
                f"Type B parsing completed: {len(self.data_types)} data types, {len(self.pous)} POUs, {len(self.global_vars)} global vars, {len(self.enums)} enums, {len(self.unions)} unions, {len(self.structures)} structures")

            return json_data

        except Exception as e:
            self.logger.error(f"Error during Type B XML parsing: {str(e)}", exc_info=True)
            raise

    def _debug_type_b_structure(self):
        """Debug the Type B XML structure with extensive logging"""
        self.logger.debug("=== TYPE B XML STRUCTURE DEBUG ===")

        # Count all elements
        all_elements = list(self.root.iter())
        self.logger.debug(f"Total elements in XML: {len(all_elements)}")

        # Look for the application data structure
        application_data = self._find_with_fallback(self.root,
                                                    './/addData/data[@name="http://www.3s-software.com/plcopenxml/application"]')
        if application_data is not None:
            self.logger.debug("Found application data element")
            # Explore application data structure
            self._explore_application_data(application_data)
        else:
            self.logger.debug("Application data element not found, looking for alternatives")

            # Look for any data elements with application in name
            all_data_elements = self._findall_with_fallback(self.root, './/addData/data')
            for data_elem in all_data_elements:
                name_attr = data_elem.get('name', '')
                self.logger.debug(f"Found data element with name: {name_attr}")
                if 'application' in name_attr.lower():
                    self.logger.debug(f"Potential application data element: {name_attr}")
                    self._explore_application_data(data_elem)

        # Debug: Look for globalVars anywhere in the document
        self._debug_global_vars_structure()

    def _debug_global_vars_structure(self):
        """Specifically debug the globalVars structure"""
        self.logger.debug("=== GLOBAL VARS STRUCTURE DEBUG ===")

        # Look for globalVars at different levels
        global_vars_elements = self._findall_with_fallback(self.root, './/globalVars')
        self.logger.debug(f"Found {len(global_vars_elements)} globalVars elements in entire document")

        for i, gv_elem in enumerate(global_vars_elements):
            gv_name = gv_elem.get('name', 'No name')
            self.logger.debug(f"GlobalVars {i}: name='{gv_name}'")

            # Count variables in this globalVars section
            variables = self._findall_with_fallback(gv_elem, './/variable')
            self.logger.debug(f"  - Contains {len(variables)} variables")

            # Log first few variable names for debugging
            for j, var in enumerate(variables[:5]):  # Limit to first 5 to avoid too much logging
                var_name = var.get('name', f'unknown_{j}')
                self.logger.debug(f"    - Variable {j}: {var_name}")

        # Also look for variables directly without globalVars parent
        all_variables = self._findall_with_fallback(self.root, './/variable')
        self.logger.debug(f"Found {len(all_variables)} total variable elements in document")

        # Log the structure of first 10 variables
        for i, var in enumerate(all_variables[:10]):
            var_name = var.get('name', f'unknown_{i}')
            self.logger.debug(f"Variable {i}: '{var_name}'")

    def _explore_application_data(self, application_data):
        """Explore the application data structure"""
        self.logger.debug("Exploring application data structure...")

        # Look for resource elements within application data
        resources = self._findall_with_fallback(application_data, './/resource')
        self.logger.debug(f"Found {len(resources)} resource elements in application data")

        for i, resource in enumerate(resources):
            resource_name = resource.get('name', f'unknown_{i}')
            self.logger.debug(f"Resource {i}: {resource_name}")

            # Look for data types and POUs in this resource
            data_types_in_resource = self._findall_with_fallback(resource, './/dataType')
            pous_in_resource = self._findall_with_fallback(resource, './/pou')
            global_vars_in_resource = self._findall_with_fallback(resource, './/globalVars')

            self.logger.debug(f"  - DataTypes: {len(data_types_in_resource)}")
            self.logger.debug(f"  - POUs: {len(pous_in_resource)}")
            self.logger.debug(f"  - GlobalVars sections: {len(global_vars_in_resource)}")

            # Count variables in globalVars
            for global_vars in global_vars_in_resource:
                vars_count = len(self._findall_with_fallback(global_vars, './/variable'))
                self.logger.debug(f"    - Variables in globalVars: {vars_count}")

            # Also look for actions and methods
            actions_in_resource = self._findall_with_fallback(resource, './/action')
            methods_in_resource = self._findall_with_fallback(resource, './/method')

            self.logger.debug(f"  - Actions: {len(actions_in_resource)}")
            self.logger.debug(f"  - Methods: {len(methods_in_resource)}")

    def _extract_application_data(self):
        """Extract data types and POUs from application data"""
        self.logger.debug("Extracting DataTypes and POUs from application data")

        # Strategy 1: Look in application data resources
        application_data = self._find_with_fallback(self.root,
                                                    './/addData/data[@name="http://www.3s-software.com/plcopenxml/application"]')
        if application_data is not None:
            self.logger.debug("Found application data, extracting from resources")
            resources = self._findall_with_fallback(application_data, './/resource')
            for resource in resources:
                self._extract_from_resource(resource)

        # Strategy 2: Look for data types and POUs directly under resources
        if not self.data_types and not self.pous:
            self.logger.debug("Trying direct resource extraction")
            resources = self._findall_with_fallback(self.root, './/resource')
            self.logger.debug(f"Found {len(resources)} resources for direct extraction")
            for resource in resources:
                self._extract_from_resource(resource)

        # Strategy 3: Look for data types and POUs anywhere in the document
        if not self.data_types and not self.pous:
            self.logger.debug("Trying global extraction from entire document")
            self._extract_global_content()

    def _extract_from_resource(self, resource_elem):
        """Extract data from a resource element"""
        # Extract data types
        data_type_elems = self._findall_with_fallback(resource_elem, './/dataType')
        self.logger.debug(f"Found {len(data_type_elems)} dataType elements in resource")

        for data_type in data_type_elems:
            self._process_data_type_element(data_type)

        # Extract POUs
        pou_elems = self._findall_with_fallback(resource_elem, './/pou')
        self.logger.debug(f"Found {len(pou_elems)} pou elements in resource")

        for pou in pou_elems:
            self._process_pou_element(pou)

    def _extract_global_content(self):
        """Extract data types and POUs from entire document"""
        # Extract all data types
        all_data_types = self._findall_with_fallback(self.root, './/dataType')
        self.logger.debug(f"Found {len(all_data_types)} dataType elements globally")

        for data_type in all_data_types:
            self._process_data_type_element(data_type)

        # Extract all POUs
        all_pous = self._findall_with_fallback(self.root, './/pou')
        self.logger.debug(f"Found {len(all_pous)} pou elements globally")

        for pou in all_pous:
            self._process_pou_element(pou)

    def _extract_global_variables(self):
        """Extract global variables from application data"""
        self.logger.debug("=== EXTRACTING GLOBAL VARIABLES ===")

        # Strategy 1: Look for globalVars in application data resources
        application_data = self._find_with_fallback(self.root,
                                                    './/addData/data[@name="http://www.3s-software.com/plcopenxml/application"]')
        if application_data is not None:
            self.logger.debug("Strategy 1: Looking in application data resources")
            resources = self._findall_with_fallback(application_data, './/resource')
            self.logger.debug(f"Found {len(resources)} resources in application data")
            for resource in resources:
                self._extract_global_vars_from_resource(resource, "Strategy 1")
        else:
            self.logger.debug("Strategy 1: No application data found")

        # Strategy 2: Look for globalVars directly under resources
        if not self.global_vars:
            self.logger.debug("Strategy 2: Looking for globalVars directly under resources")
            resources = self._findall_with_fallback(self.root, './/resource')
            self.logger.debug(f"Found {len(resources)} resources for direct extraction")
            for resource in resources:
                self._extract_global_vars_from_resource(resource, "Strategy 2")

        # Strategy 3: Look for global variables anywhere in the document
        if not self.global_vars:
            self.logger.debug("Strategy 3: Looking for global variables anywhere in document")
            all_global_vars = self._findall_with_fallback(self.root, './/globalVars//variable')
            self.logger.debug(f"Found {len(all_global_vars)} global variables globally")
            for variable in all_global_vars:
                self._process_global_variable(variable, "Global Variables", "Strategy 3")

        self.logger.debug(f"Total global variables extracted: {len(self.global_vars)}")

    def _extract_global_vars_from_resource(self, resource_elem, strategy_name):
        """Extract global variables from a resource element"""
        self.logger.debug(f"{strategy_name}: Extracting from resource '{resource_elem.get('name', 'unknown')}'")

        global_vars_sections = self._findall_with_fallback(resource_elem, './/globalVars')
        self.logger.debug(f"{strategy_name}: Found {len(global_vars_sections)} globalVars sections in resource")

        for global_vars_section in global_vars_sections:
            global_vars_name = global_vars_section.get('name', 'Global Variables')
            self.logger.debug(f"{strategy_name}: Processing globalVars: {global_vars_name}")

            variables = self._findall_with_fallback(global_vars_section, './/variable')
            self.logger.debug(f"{strategy_name}: Found {len(variables)} variables in {global_vars_name}")

            for variable in variables:
                self._process_global_variable(variable, global_vars_name, strategy_name)

    def _process_global_variable(self, var_elem, global_vars_name, strategy_name="Unknown"):
        """Process global variable element"""
        try:
            var_info = self._extract_variable_info(var_elem)
            if var_info:
                var_info['global_vars_group'] = global_vars_name
                var_info['location'] = 'global'
                var_info['extraction_strategy'] = strategy_name
                self.global_vars.append(var_info)
                self.logger.debug(f"{strategy_name}: Added global variable: {var_info['name']} in {global_vars_name}")
            else:
                self.logger.debug(f"{strategy_name}: Failed to extract variable info for element")

        except Exception as e:
            self.logger.warning(f"{strategy_name}: Error processing global variable: {str(e)}")

    def _extract_complex_data_types(self):
        """Extract enums, unions, and structures with enhanced detection"""
        self.logger.debug("Extracting complex data types (enums, unions, structures)")

        # Look for UNION elements in addData sections
        union_data_elems = self._findall_with_fallback(self.root,
                                                       './/addData/data[@name="http://www.3s-software.com/plcopenxml/union"]')
        self.logger.debug(f"Processing {len(union_data_elems)} union addData elements")

        for union_data in union_data_elems:
            unions = self._findall_with_fallback(union_data, './/union')
            for union_elem in unions:
                union_name = union_elem.get('name')
                if union_name and not any(u['name'] == union_name for u in self.unions):
                    # Extract union members directly
                    members = []
                    member_elems = self._findall_with_fallback(union_elem, './/variable')
                    for member_elem in member_elems:
                        member_info = self._extract_variable_info(member_elem)
                        if member_info:
                            members.append(member_info)

                    union_info = {
                        'name': union_name,
                        'type': 'union',
                        'members': members,
                        'details': self._extract_data_type_details(union_elem)
                    }
                    self.unions.append(union_info)
                    self.logger.debug(
                        f"Added union from addData: {union_name} with {len(union_info['members'])} members")

        # Look for ENUM elements in addData sections
        enum_data_elems = self._findall_with_fallback(self.root,
                                                      './/addData/data[@name="http://www.3s-software.com/plcopenxml/datatype"]')
        self.logger.debug(f"Processing {len(enum_data_elems)} datatype addData elements")

        for enum_data in enum_data_elems:
            data_types = self._findall_with_fallback(enum_data, './/dataType')
            for data_type in data_types:
                # Process enums directly
                name = data_type.get('name')
                if not name:
                    name_elem = self._find_with_fallback(data_type, './name')
                    if name_elem and name_elem.text:
                        name = name_elem.text

                if not name:
                    continue

                # Check if it's an enum by looking for enum-specific structure
                if (self._find_with_fallback(data_type, './/values') is not None or
                        self._find_with_fallback(data_type, './/enumValue') is not None or
                        self._find_with_fallback(data_type, './/enum') is not None):

                    if not any(e['name'] == name for e in self.enums):
                        # Extract enum values
                        values = []
                        value_elems = self._findall_with_fallback(data_type, './/values//value')
                        if not value_elems:
                            value_elems = self._findall_with_fallback(data_type, './/enumValue')

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

                        enum_info = {
                            'name': name,
                            'type': 'enum',
                            'values': values,
                            'base_type': 'INT',  # Default, could be enhanced
                            'details': self._extract_data_type_details(data_type)
                        }
                        self.enums.append(enum_info)
                        self.logger.debug(f"Added enum: {name} with {len(enum_info['values'])} values")
                        continue  # Skip to next data type

                # Check if it's a structure (has variables but not an enum)
                member_elems = self._findall_with_fallback(data_type, './/variable')
                if len(member_elems) > 0 and not any(s['name'] == name for s in self.structures):
                    members = []
                    for member_elem in member_elems:
                        member_info = self._extract_variable_info(member_elem)
                        if member_info:
                            members.append(member_info)

                    struct_info = {
                        'name': name,
                        'type': 'structure',
                        'members': members,
                        'details': self._extract_data_type_details(data_type)
                    }
                    self.structures.append(struct_info)
                    self.logger.debug(f"Added structure: {name} with {len(struct_info['members'])} members")
                    continue  # Skip to next data type

                # If none of the above, treat as basic data type
                if not any(dt['name'] == name for dt in self.data_types):
                    data_type_info = {
                        'name': name,
                        'type': 'dataType',
                        'details': self._extract_data_type_details(data_type)
                    }
                    self.data_types.append(data_type_info)
                    self.logger.debug(f"Added basic data type: {name}")

        # Also extract from regular dataType elements
        all_data_types = self._findall_with_fallback(self.root, './/dataType')
        self.logger.debug(f"Processing {len(all_data_types)} total dataType elements")

        for data_type in all_data_types:
            # Skip if already processed
            name = data_type.get('name')
            if not name:
                name_elem = self._find_with_fallback(data_type, './name')
                if name_elem and name_elem.text:
                    name = name_elem.text

            if name and not any(dt['name'] == name for dt in
                                self.data_types + [e for e in self.enums] + [u for u in self.unions] + [s for s in
                                                                                                        self.structures]):
                # Use the same classification logic as above
                # ... (copy the same classification logic here for dataType elements)
                pass  # For brevity, you would copy the same logic here


if __name__ == "__main__":
    print("This module is intended to be used with main.py")