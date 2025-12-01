"""
Debug script for testing XML parser - Enhanced version
"""

import logging
import sys
from pathlib import Path
from lxml import etree

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger('DebugParser')

def dump_data_type_details(file_path, max_to_examine=10):
    """Dump detailed information about dataType elements"""
    logger.info(f"Examining dataType elements in: {file_path}")

    try:
        tree = etree.parse(file_path)
        root = tree.getroot()

        # Find all dataType elements
        namespace = '{http://www.plcopen.org/xml/tc6_0200}'
        data_types = root.findall(f'.//{namespace}dataType')

        logger.info(f"Found {len(data_types)} dataType elements")

        for i, dt in enumerate(data_types[:max_to_examine]):
            name = dt.get('name', 'Unknown')
            logger.info(f"\n{'='*60}")
            logger.info(f"DataType {i+1}: {name}")
            logger.info(f"{'='*60}")

            # Show all attributes
            logger.info(f"Attributes:")
            for attr_name, attr_value in dt.attrib.items():
                logger.info(f"  {attr_name}: {attr_value}")

            # Show all child elements
            logger.info(f"Child elements:")
            for child in dt:
                child_tag = etree.QName(child.tag).localname

                if child_tag == 'baseType':
                    # Get the type from baseType element
                    base_type_value = child.get('name', 'Unknown')
                    logger.info(f"  baseType: name='{base_type_value}'")

                    # Check if it's an enum
                    if base_type_value == 'ENUM':
                        logger.info(f"    ^^^ THIS IS AN ENUM!")
                        # Look for values
                        for subchild in child:
                            subchild_tag = etree.QName(subchild.tag).localname
                            if subchild_tag == 'addData':
                                logger.info(f"    addData found - may contain enum values")
                                # Try to find values in addData
                                for data in subchild:
                                    data_tag = etree.QName(data.tag).localname
                                    logger.info(f"      {data_tag}: {data.attrib}")

                    # Also check for enum values directly
                    values = child.findall(f'.//{namespace}value')
                    if values:
                        logger.info(f"    Found {len(values)} enum values:")
                        for val in values[:5]:
                            val_name = val.get('name', 'Unknown')
                            val_value = val.get('value', 'Unknown')
                            logger.info(f"      {val_name} = {val_value}")
                        if len(values) > 5:
                            logger.info(f"      ... and {len(values) - 5} more")

                elif child_tag == 'addData':
                    logger.info(f"  addData: {len(child)} sub-elements")
                    # Look for enum values in addData
                    for subchild in child:
                        subchild_tag = etree.QName(subchild.tag).localname
                        logger.info(f"    {subchild_tag}: {subchild.attrib}")

                        # Check for values
                        values = subchild.findall(f'.//{namespace}value')
                        if values:
                            logger.info(f"      Found {len(values)} values in {subchild_tag}")
                            for val in values[:3]:
                                logger.info(f"        {val.get('name')} = {val.get('value')}")

                elif child_tag == 'initialValue':
                    init_value = child.text if child.text else 'None'
                    logger.info(f"  initialValue: {init_value}")

                else:
                    logger.info(f"  {child_tag}: {len(child)} sub-elements")

                    # Check if this child contains values (for enums)
                    values = child.findall(f'.//{namespace}value')
                    if values:
                        logger.info(f"    Contains {len(values)} values:")
                        for val in values[:3]:
                            logger.info(f"      {val.get('name')} = {val.get('value')}")
                        if len(values) > 3:
                            logger.info(f"      ... and {len(values) - 3} more")

        if len(data_types) > max_to_examine:
            logger.info(f"\n... and {len(data_types) - max_to_examine} more dataType elements")

    except Exception as e:
        logger.error(f"Failed to examine dataType elements: {str(e)}", exc_info=True)


def dump_all_elements_by_type(file_path):
    """Dump counts of all element types"""
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Element counts in: {file_path}")
    logger.info(f"{'=' * 80}")

    try:
        tree = etree.parse(file_path)
        root = tree.getroot()

        namespace = '{http://www.plcopen.org/xml/tc6_0200}'

        # Count different element types
        element_counts = {}
        comment_count = 0
        other_non_element_count = 0

        for elem in root.iter():
            # Check if this is a comment node
            if isinstance(elem, etree._Comment):
                comment_count += 1
                continue

            # Check if this is a processing instruction or other non-element node
            if not isinstance(elem, etree._Element):
                other_non_element_count += 1
                continue

            # It's a regular element - get its tag name
            try:
                tag_name = etree.QName(elem.tag).localname
                element_counts[tag_name] = element_counts.get(tag_name, 0) + 1
            except (ValueError, TypeError) as e:
                # Log but skip unusual elements
                logger.debug(f"Skipping element with unusual tag '{elem.tag}': {e}")
                other_non_element_count += 1

        # Sort by count
        sorted_counts = sorted(element_counts.items(), key=lambda x: x[1], reverse=True)

        logger.info(f"Total regular elements: {sum(element_counts.values())}")
        logger.info(f"Comment nodes: {comment_count}")
        logger.info(f"Other non-element nodes: {other_non_element_count}")
        logger.info(f"Unique element types: {len(element_counts)}")
        logger.info(f"\nTop 30 element types:")
        for tag, count in sorted_counts[:30]:
            logger.info(f"  {tag}: {count}")

        # Specifically look for enum-related elements
        logger.info(f"\nLooking for enum-related elements:")

        # Check for ENUM baseType elements
        enum_base_types = root.findall(f'.//{namespace}baseType[@name="ENUM"]')
        logger.info(f"  baseType elements with name='ENUM': {len(enum_base_types)}")

        # Check for value elements (enum values)
        value_elements = root.findall(f'.//{namespace}value')
        logger.info(f"  value elements: {len(value_elements)}")

        if value_elements:
            logger.info(f"  First few value elements:")
            for val in value_elements[:5]:
                logger.info(f"    name='{val.get('name')}', value='{val.get('value')}'")

        # Look for structures and unions
        struct_elements = root.findall(f'.//{namespace}struct')
        logger.info(f"  struct elements: {len(struct_elements)}")

        union_elements = root.findall(f'.//{namespace}union')
        logger.info(f"  union elements: {len(union_elements)}")

        # Look for variable elements (in structs/unions)
        variable_elements = root.findall(f'.//{namespace}variable')
        logger.info(f"  variable elements: {len(variable_elements)}")

    except Exception as e:
        logger.error(f"Failed to count elements: {str(e)}", exc_info=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        dump_data_type_details(file_path, max_to_examine=5)
        dump_all_elements_by_type(file_path)
    else:
        logger.error("Please provide an XML file path as argument")
        logger.info("Usage: python debug_parser.py <path_to_xml_file>")