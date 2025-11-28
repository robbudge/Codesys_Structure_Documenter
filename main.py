#!/usr/bin/env python3
"""
Main entry point for Codesys PLCopen XML Documentation Generator
Enhanced detection for all three XML formats with modular parsers
"""

import logging
import sys
import os
import re
from pathlib import Path
from gui import XMLParserGUI
from xml_parse_type_a import TypeAParser
from xml_parse_type_b import TypeBParser
from xml_parse_type_c import TypeCParser


class CodesysXMLDocumentationGenerator:
    """Main class for generating documentation from Codesys PLCopen XML files"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.current_parser = None
        self.logger.debug("CodesysXMLDocumentationGenerator initialized")

    def _setup_logging(self):
        """Setup extensive logging with detailed format"""
        logger = logging.getLogger('CodesysXMLDocGenerator')
        logger.setLevel(logging.DEBUG)

        # Create formatter with detailed information
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler for debug logs
        file_handler = logging.FileHandler('codesys_xml_parser.log', mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def detect_xml_type_and_structure(self, xml_file_path):
        """
        Detect XML type and analyze structure for all three formats

        Args:
            xml_file_path (str): Path to XML file

        Returns:
            dict: Detection results with counts and type
        """
        self.logger.debug(f"detect_xml_type_and_structure called with file: {xml_file_path}")

        try:
            with open(xml_file_path, 'r', encoding='utf-8') as file:
                content = file.read(50000)  # Read more content for better analysis

            detection_result = {
                'file_path': xml_file_path,
                'file_size': os.path.getsize(xml_file_path),
                'type': 'unknown',
                'structures_found': {},
                'element_counts': {},
                'raw_content_sample': content[:1000]  # First 1000 chars for debugging
            }

            # Check for Type A: <project><types><dataTypes>
            if '<types>' in content and '<dataTypes>' in content:
                detection_result['structures_found']['type_a'] = True
                detection_result['element_counts']['dataTypes'] = content.count('<dataType')
                detection_result['element_counts']['pous'] = content.count('<pou')
                self.logger.debug(
                    f"Type A elements - dataTypes: {content.count('<dataType')}, pous: {content.count('<pou')}")

            # Check for Type B: <project><addData><data name="http://www.3s-software.com/plcopenxml/application"
            if 'http://www.3s-software.com/plcopenxml/application' in content:
                detection_result['structures_found']['type_b'] = True
                detection_result['element_counts']['resources'] = content.count('<resource')
                self.logger.debug(f"Type B elements - resources: {content.count('<resource')}")

            # Check for Type C: <project><instances><configurations><configuration
            if '<instances>' in content and '<configurations>' in content and '<configuration' in content:
                detection_result['structures_found']['type_c'] = True
                detection_result['element_counts']['configurations'] = content.count('<configuration')
                detection_result['element_counts']['resources'] = content.count('<resource')
                self.logger.debug(
                    f"Type C elements - configurations: {content.count('<configuration')}, resources: {content.count('<resource')}")

            # Determine primary type based on content analysis
            if detection_result['structures_found'].get('type_a'):
                if detection_result['element_counts'].get('dataTypes', 0) > 0 or detection_result['element_counts'].get(
                        'pous', 0) > 0:
                    detection_result['type'] = 'type_a'
                    self.logger.info(
                        f"Detected Type A (Partial Export) - DataTypes: {detection_result['element_counts'].get('dataTypes', 0)}, POUs: {detection_result['element_counts'].get('pous', 0)}")

            elif detection_result['structures_found'].get('type_b'):
                detection_result['type'] = 'type_b'
                self.logger.info(
                    f"Detected Type B (Application Export) - Resources: {detection_result['element_counts'].get('resources', 0)}")

            elif detection_result['structures_found'].get('type_c'):
                detection_result['type'] = 'type_c'
                self.logger.info(
                    f"Detected Type C (Full Project Export) - Configurations: {detection_result['element_counts'].get('configurations', 0)}, Resources: {detection_result['element_counts'].get('resources', 0)}")

            else:
                self.logger.warning("Could not determine XML type - unknown structure")
                # Log sample content for debugging
                self.logger.debug(f"Content sample: {content[:500]}")

            return detection_result

        except Exception as e:
            self.logger.error(f"Error analyzing XML structure in {xml_file_path}: {str(e)}", exc_info=True)
            return {
                'file_path': xml_file_path,
                'type': 'error',
                'error': str(e)
            }

    def parse_xml_file(self, xml_file_path):
        """
        Parse XML file based on detected type and return standardized JSON

        Args:
            xml_file_path (str): Path to XML file

        Returns:
            tuple: (parser_object, standardized_json_data)
        """
        self.logger.debug(f"parse_xml_file called with: {xml_file_path}")

        # First, detect the XML type and structure
        detection_result = self.detect_xml_type_and_structure(xml_file_path)
        self.logger.info(f"XML detection result: {detection_result}")

        try:
            xml_type = detection_result['type']

            if xml_type == 'type_a':
                self.logger.info(f"Initializing TypeAParser for Type A: {xml_file_path}")
                self.current_parser = TypeAParser(xml_file_path)
                json_data = self.current_parser.parse_to_json()
                return self.current_parser, json_data

            elif xml_type == 'type_b':
                self.logger.info(f"Initializing TypeBParser for Type B: {xml_file_path}")
                self.current_parser = TypeBParser(xml_file_path)
                json_data = self.current_parser.parse_to_json()
                return self.current_parser, json_data

            elif xml_type == 'type_c':
                self.logger.info(f"Initializing TypeCParser for Type C: {xml_file_path}")
                self.current_parser = TypeCParser(xml_file_path)
                json_data = self.current_parser.parse_to_json()
                return self.current_parser, json_data

            else:
                self.logger.error(f"Unsupported or unknown XML type: {xml_type}")
                raise ValueError(f"Unsupported XML file format: {xml_type}")

        except Exception as e:
            self.logger.error(f"Error parsing XML file {xml_file_path}: {str(e)}", exc_info=True)
            raise


def main():
    """Main function to start the application"""
    print("Codesys PLCopen XML Documentation Generator")
    print("===========================================")
    print("Enhanced Detection for All XML Formats")
    print("Supported Types:")
    print("  - Type A: Partial Export (<project><types><dataTypes>)")
    print("  - Type B: Application Export (<project><addData><data name='application'>)")
    print("  - Type C: Full Project Export (<project><instances><configurations>)")

    # Initialize the main generator
    generator = CodesysXMLDocumentationGenerator()
    generator.logger.info("Application started - All XML types supported")

    try:
        # Start GUI
        app = XMLParserGUI(generator)
        app.logger.info("GUI initialized successfully")
        app.run()

    except Exception as e:
        generator.logger.critical(f"Application crashed: {str(e)}", exc_info=True)
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()