"""
Type C XML Parser for Codesys Full Project Exports
Handles XML files with <project><instances><configurations><configuration><resource> structure
"""

from xml_parse_common import CommonXMLParser
import logging


class TypeCParser(CommonXMLParser):
    """Parser for Type C Codesys XML exports (Full Project Export)"""

    def __init__(self, xml_file_path):
        self.export_type = "type_c"
        super().__init__(xml_file_path)
        self.logger = logging.getLogger('CodesysXMLDocGenerator.TypeCParser')
        self.logger.debug(f"TypeCParser initialized with file: {xml_file_path}")

        # Additional project information for Type C
        self.plc_name = None
        self.app_name = None

    def parse_to_json(self):
        """
        Parse the Type C XML export and return standardized JSON

        Returns:
            dict: Standardized JSON structure with DataTypes, POUs, etc.
        """
        self.logger.debug("Starting Type C XML parsing process")

        try:
            # Extract project information
            self._extract_project_info()

            # Extract data from configurations and resources
            self._extract_from_configurations()

            # Extract global variables
            self._extract_global_variables()

            # Extract complex data types
            self._extract_complex_data_types()

            # Return standardized JSON with additional project info
            json_data = self._get_standardized_json()

            # Add Type C specific information
            json_data["plc_name"] = self.plc_name
            json_data["app_name"] = self.app_name

            self.logger.info(
                f"Type C parsing completed: {len(self.data_types)} data types, {len(self.pous)} POUs, {len(self.global_vars)} global vars")

            return json_data

        except Exception as e:
            self.logger.error(f"Error during Type C XML parsing: {str(e)}", exc_info=True)
            raise

    def _extract_project_info(self):
        """Extract PLC and application names from Type C structure"""
        self.logger.debug("Extracting project information for Type C")

        # Find configuration element
        config_elem = self._find_with_fallback(self.root, './/configuration')
        if config_elem is not None:
            config_name_elem = self._find_with_fallback(config_elem, './name')
            if config_name_elem is not None and config_name_elem.text:
                self.plc_name = config_name_elem.text
                self.logger.debug(f"PLC Name: {self.plc_name}")

        # Find resource element
        resource_elem = self._find_with_fallback(self.root, './/resource')
        if resource_elem is not None:
            resource_name_elem = self._find_with_fallback(resource_elem, './name')
            if resource_name_elem is not None and resource_name_elem.text:
                self.app_name = resource_name_elem.text
                self.logger.debug(f"Application Name: {self.app_name}")

    def _extract_from_configurations(self):
        """Extract data from configurations and resources (main location for Type C)"""
        self.logger.debug("Extracting from configurations section")

        # Find all configurations
        configurations = self._findall_with_fallback(self.root, './/configuration')
        self.logger.debug(f"Found {len(configurations)} configurations")

        for config in configurations:
            config_name_elem = self._find_with_fallback(config, './name')
            config_name = config_name_elem.text if config_name_elem is not None else "Unknown"
            self.logger.debug(f"Processing configuration: {config_name}")

            # Extract from resources in this configuration
            resources = self._findall_with_fallback(config, './/resource')
            for resource in resources:
                resource_name_elem = self._find_with_fallback(resource, './name')
                resource_name = resource_name_elem.text if resource_name_elem is not None else "Unknown"
                self.logger.debug(f"Processing resource: {resource_name}")

                self._extract_from_resource(resource, f"{config_name}/{resource_name}")

    def _extract_from_resource(self, resource_elem, context_path):
        """Extract data from a resource element with context"""
        # Extract data types
        data_type_elems = self._findall_with_fallback(resource_elem, './/dataType')
        self.logger.debug(f"Found {len(data_type_elems)} dataType elements in resource {context_path}")

        for data_type in data_type_elems:
            self._process_data_type_element(data_type)

        # Extract POUs
        pou_elems = self._findall_with_fallback(resource_elem, './/pou')
        self.logger.debug(f"Found {len(pou_elems)} pou elements in resource {context_path}")

        for pou in pou_elems:
            self._process_pou_element(pou)

        # Extract tasks (specific to Type C)
        task_elems = self._findall_with_fallback(resource_elem, './/task')
        self.logger.debug(f"Found {len(task_elems)} task elements in resource {context_path}")

        # Note: We're currently ignoring tasks as per requirements, but we log them

    def _extract_global_variables(self):
        """Extract global variables for Type C"""
        self.logger.debug("Extracting global variables for Type C")

        # Look for globalVars in resources
        resources = self._findall_with_fallback(self.root, './/resource')
        for resource in resources:
            resource_name_elem = self._find_with_fallback(resource, './name')
            resource_name = resource_name_elem.text if resource_name_elem is not None else "Unknown Resource"

            global_vars_sections = self._findall_with_fallback(resource, './/globalVars')
            for global_vars_section in global_vars_sections:
                global_vars_name = global_vars_section.get('name', f'Global Variables - {resource_name}')
                variables = self._findall_with_fallback(global_vars_section, './/variable')

                self.logger.debug(f"Found {len(variables)} global variables in {global_vars_name}")

                for variable in variables:
                    self._process_global_variable(variable, global_vars_name)

    def _process_global_variable(self, var_elem, global_vars_name):
        """Process global variable element"""
        try:
            var_info = self._extract_variable_info(var_elem)
            if var_info:
                var_info['global_vars_group'] = global_vars_name
                var_info['location'] = 'global'
                self.global_vars.append(var_info)
                self.logger.debug(f"Added global variable: {var_info['name']} in {global_vars_name}")

        except Exception as e:
            self.logger.warning(f"Error processing global variable: {str(e)}")

    def _extract_complex_data_types(self):
        """Extract enums, unions, and structures for Type C"""
        self.logger.debug("Extracting complex data types for Type C")

        # Look in resources
        resources = self._findall_with_fallback(self.root, './/resource')
        for resource in resources:
            data_types = self._findall_with_fallback(resource, './/dataType')
            for data_type in data_types:
                self._process_complex_data_type(data_type)

        # Also look anywhere in document as fallback
        all_data_types = self._findall_with_fallback(self.root, './/dataType')
        for data_type in all_data_types:
            name = data_type.get('name')
            if not name:
                name_elem = self._find_with_fallback(data_type, './name')
                if name_elem and name_elem.text:
                    name = name_elem.text

            if name and not any(dt['name'] == name for dt in
                                self.data_types + [e for e in self.enums] + [u for u in self.unions] + [s for s in
                                                                                                        self.structures]):
                self._process_complex_data_type(data_type)


if __name__ == "__main__":
    print("This module is intended to be used with main.py")