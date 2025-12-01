"""
Mermaid Utilities - Helper functions for Mermaid diagram generation
"""

import re
import logging


class MermaidUtils:
    """Utility class for Mermaid diagram generation"""

    @staticmethod
    def sanitize_node_id(name: str) -> str:
        """
        Sanitize a string to be a valid Mermaid node ID.
        Removes or replaces characters that break Mermaid syntax.
        """
        if not name:
            return "node"

        # Replace problematic characters with underscores
        sanitized = str(name)

        # Replace parentheses, brackets, special chars
        sanitized = re.sub(r'[()\[\]{}<>]', '_', sanitized)

        # Replace other problematic characters
        sanitized = re.sub(r'[#@$%^&*+=|\\/:";\',.?`~]', '_', sanitized)

        # Replace spaces and hyphens with underscores
        sanitized = sanitized.replace(' ', '_').replace('-', '_')

        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')

        # Ensure it starts with a letter (Mermaid requirement)
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'node_' + sanitized

        # Ensure it's not empty
        if not sanitized:
            sanitized = 'node'

        return sanitized

    @staticmethod
    def sanitize_label_text(text: str) -> str:
        """
        Sanitize text for Mermaid labels.
        Escapes quotes and handles line breaks.
        """
        if not text:
            return ""

        # Escape double quotes
        sanitized = text.replace('"', '&quot;')

        # Escape single quotes
        sanitized = sanitized.replace("'", "&apos;")

        # Convert line breaks to HTML <br>
        sanitized = sanitized.replace('\n', '<br>')

        return sanitized

    @staticmethod
    def create_safe_node_id(base_name: str, counter: int = None) -> str:
        """
        Create a safe node ID with optional counter.
        """
        safe_id = MermaidUtils.sanitize_node_id(base_name)
        if counter is not None:
            safe_id = f"{safe_id}_{counter}"
        return safe_id

    @staticmethod
    def validate_mermaid_code(code: str, logger=None) -> bool:
        """
        Basic validation of Mermaid code.
        Returns True if code appears valid, False if obvious issues found.
        """
        if not code:
            if logger:
                logger.warning("Empty Mermaid code")
            return False

        # Check for common issues
        issues = []

        # Check for unclosed brackets in node definitions
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Check for node definitions with unclosed quotes/brackets
            if '["' in line and not line.endswith('"]'):
                # Count quotes to see if they're balanced
                if line.count('"') % 2 != 0:
                    issues.append(f"Line {i}: Unbalanced quotes in node definition")

            # Check for special characters in node IDs
            if '[' in line and ']' in line:
                node_id = line.split('[')[0].strip()
                if re.search(r'[()\[\]{}]', node_id):
                    issues.append(f"Line {i}: Node ID contains special characters: {node_id}")

        if issues and logger:
            for issue in issues:
                logger.warning(f"Mermaid validation: {issue}")

        return len(issues) == 0