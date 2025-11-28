"""
Type A XML Parser for Codesys Partial Exports
Handles XML files with <project><types><dataTypes> structure
"""

from xml_parse_common import CommonXMLParser
import logging


class TypeAParser(CommonXMLParser):
    """Parser for Type A Codesys XML exports (Partial Export)"""

    def __init__(self, xml_file_path):
        self.export_type = "type_a"
        super().__init__(xml_file_path)
        self.logger = logging.getLogger('CodesysXMLDocGenerator.TypeAParser')
        self.logger.debug(f"TypeAParser initialized with file: {xml_file_path}")

    def parse_to_json(self):
        """
        Parse the Type A XML export and return standardized JSON

        Returns:
            dict: Standardized JSON structure with DataTypes, POUs, etc.
        """
        self.logger.debug("Starting Type A XML parsing process")

        try:
            # Extract from types section (main location for Type A)
            self._extract_from_types_section()

            # Extract global variables if present
            self._extract_global_variables()

            # Extract complex data types
            self._extract_complex_data_types()

            # Return standardized JSON
            json_data = self._get_standardized_json()

            self.logger.info(
                f"Type A parsing completed: {len(self.data_types)} data types, {len(self.pous)} POUs, {len(self.global_vars)} global vars")

            return json_data

        except Exception as e:
            self.logger.error(f"Error during Type A XML parsing: {str(e)}", exc_info=True)
            raise

    def _extract_from_types_section(self):
        """Extract data from the types section (main location for Type A)"""
        self.logger.debug("Extracting from types section")

        # Find types element
        types_elem = self._find_with_fallback(self.root, './/types')
        if types_elem is None:
            self.logger.warning("No <types> element found in Type A XML")
            return

        # Extract data types
        data_types_elem = self._find_with_fallback(types_elem, './dataTypes')
        if data_types_elem is not None:
            data_type_elems = self._findall_with_fallback(data_types_elem, './dataType')
            for data_type in data_type_elems:
                self._process_data_type_element(data_type)

        # Extract POUs
        pous_elem = self._find_with_fallback(types_elem, './pous')
        if pous_elem is not None:
            pou_elems = self._findall_with_fallback(pous_elem, './pou')
            for pou in pou_elems:
                self._process_pou_element(pou)

    def _extract_global_variables(self):
        """Extract global variables for Type A"""
        self.logger.debug("Extracting global variables for Type A")

        # Look for globalVars in types section
        types_elem = self._find_with_fallback(self.root, './/types')
        if types_elem is not None:
            global_vars_sections = self._findall_with_fallback(types_elem, './/globalVars')
            for global_vars_section in global_vars_sections:
                global_vars_name = global_vars_section.get('name', 'Global Variables')
                variables = self._findall_with_fallback(global_vars_section, './/variable')
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
        """Extract enums, unions, and structures for Type A"""
        self.logger.debug("Extracting complex data types for Type A")

        # Look in types section first
        types_elem = self._find_with_fallback(self.root, './/types')
        if types_elem is not None:
            data_types = self._findall_with_fallback(types_elem, './/dataType')
            for data_type in data_types:
                self._process_complex_data_type(data_type)

        # Also look anywhere in document
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