"""
Structure resolver for recursive type resolution
"""

import logging
import re
from typing import Dict, List, Optional, Set
from data_models import XmlExport, StructureType, StructureMember, EnumType


class StructureResolver:
    """Recursively resolves structure types and their dependencies"""

    def __init__(self, xml_export: XmlExport, logger=None):
        self.xml_export = xml_export
        self.logger = logger or logging.getLogger(__name__)
        self.resolved_structures = {}
        self.resolved_unions = {}

    def resolve_all(self):
        """Resolve all structures and unions recursively"""
        self.logger.info("Starting recursive structure resolution...")

        # First pass: collect all structures and unions
        all_structures = {}
        for struct in self.xml_export.structures:
            all_structures[struct.name] = struct
        for union in self.xml_export.unions:
            all_structures[union.name] = union

        # Second pass: resolve each structure/union
        for name, structure in all_structures.items():
            if structure.is_union:
                self._resolve_union_recursive(name, structure, visited=set())
            else:
                self._resolve_structure_recursive(name, structure, visited=set())

        self.logger.info(f"Resolved {len(self.resolved_structures)} structures and {len(self.resolved_unions)} unions")
        return self.resolved_structures, self.resolved_unions

    def _resolve_structure_recursive(self, name: str, structure: StructureType, visited: set) -> StructureType:
        """Recursively resolve a structure and all its nested types"""
        if name in visited:
            self.logger.warning(f"Circular reference detected for structure: {name}")
            return structure

        if name in self.resolved_structures:
            return self.resolved_structures[name]

        visited.add(name)
        self.logger.debug(f"Resolving structure: {name}")

        # Create a deep copy to avoid modifying original
        resolved = StructureType(
            name=structure.name,
            members=[],
            is_union=False,
            parent_structure=structure.parent_structure
        )

        # Resolve each member
        for member in structure.members:
            resolved_member = StructureMember(
                name=member.name,
                type=member.type,
                initial_value=member.initial_value
            )

            # Check if this member type is another structure/union
            member_type = member.type.strip()

            # Handle array types
            array_match = re.match(r'^ARRAY\[.*\] OF (.*)$', member_type)
            if array_match:
                member_type = array_match.group(1)

            # Handle pointer types
            if member_type.startswith('POINTER TO '):
                member_type = member_type[11:]

            # Check if this is a known structure or union
            found_nested = None
            for struct in self.xml_export.structures:
                if struct.name == member_type:
                    found_nested = struct
                    break

            if not found_nested:
                for union in self.xml_export.unions:
                    if union.name == member_type:
                        found_nested = union
                        break

            if found_nested:
                # Recursively resolve the nested structure
                if found_nested.is_union:
                    nested_resolved = self._resolve_union_recursive(member_type, found_nested, visited.copy())
                else:
                    nested_resolved = self._resolve_structure_recursive(member_type, found_nested, visited.copy())

                # Add to nested structures
                nested_resolved.parent_structure = name
                resolved.nested_structures.append(nested_resolved)

                # Update member type to show it's a nested structure
                resolved_member.type = f"{member_type} (nested structure)"
                resolved_member.is_nested_structure = True
                resolved_member.nested_structure_ref = nested_resolved.name

            resolved.members.append(resolved_member)

        self.resolved_structures[name] = resolved
        visited.remove(name)

        return resolved

    def _resolve_union_recursive(self, name: str, union: StructureType, visited: set) -> StructureType:
        """Recursively resolve a union and all its nested types"""
        if name in visited:
            self.logger.warning(f"Circular reference detected for union: {name}")
            return union

        if name in self.resolved_unions:
            return self.resolved_unions[name]

        visited.add(name)
        self.logger.debug(f"Resolving union: {name}")

        # Create a deep copy
        resolved = StructureType(
            name=union.name,
            members=[],
            is_union=True,
            parent_structure=union.parent_structure
        )

        # Resolve each member
        for member in union.members:
            resolved_member = StructureMember(
                name=member.name,
                type=member.type,
                initial_value=member.initial_value
            )

            # Check for nested structures in union members
            member_type = member.type.strip()

            found_nested = None
            for struct in self.xml_export.structures:
                if struct.name == member_type:
                    found_nested = struct
                    break

            if not found_nested:
                for union_item in self.xml_export.unions:
                    if union_item.name == member_type:
                        found_nested = union_item
                        break

            if found_nested:
                # Recursively resolve the nested structure
                if found_nested.is_union:
                    nested_resolved = self._resolve_union_recursive(member_type, found_nested, visited.copy())
                else:
                    nested_resolved = self._resolve_structure_recursive(member_type, found_nested, visited.copy())

                nested_resolved.parent_structure = name
                resolved.nested_structures.append(nested_resolved)

                resolved_member.type = f"{member_type} (nested structure)"
                resolved_member.is_nested_structure = True
                resolved_member.nested_structure_ref = nested_resolved.name

            resolved.members.append(resolved_member)

        self.resolved_unions[name] = resolved
        visited.remove(name)

        return resolved

    def get_structure_hierarchy(self, structure_name: str) -> Dict:
        """Get complete hierarchy for a structure"""
        if structure_name in self.resolved_structures:
            structure = self.resolved_structures[structure_name]
        elif structure_name in self.resolved_unions:
            structure = self.resolved_unions[structure_name]
        else:
            return {}

        hierarchy = {
            'name': structure.name,
            'type': 'union' if structure.is_union else 'struct',
            'members': [],
            'nested': []
        }

        for member in structure.members:
            hierarchy['members'].append({
                'name': member.name,
                'type': member.type,
                'is_nested': getattr(member, 'is_nested_structure', False)
            })

        for nested in structure.nested_structures:
            hierarchy['nested'].append(self.get_structure_hierarchy(nested.name))

        return hierarchy