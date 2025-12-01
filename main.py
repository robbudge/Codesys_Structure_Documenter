"""
Main entry point for Codesys XML Documentation Generator
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('codesys_export.log', mode='w')
    ]
)

logger = logging.getLogger('CodesysXMLDocGenerator')

def main():
    """Main function"""
    try:
        logger.info("Starting Codesys XML Documentation Generator")

        # Import here to avoid circular imports
        from gui import CodesysXmlDocumenter

        # Create and run GUI
        app = CodesysXmlDocumenter()
        app.run()

        logger.info("Application closed")

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()