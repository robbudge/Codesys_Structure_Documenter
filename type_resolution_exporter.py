# Create a new file: type_resolution_exporter.py

from typing import Dict, List, Optional
from data_models import *


class TypeResolutionExporter:
    """Exporter that shows type relationships and dependencies"""

    def __init__(self, xml_export: XmlExport):
        self.xml_export = xml_export
        self.type_registry = xml_export.get_all_types()

        # Resolve all references
        xml_export.resolve_all_type_references()

    def export_hierarchical_structure(self) -> str:
        """Export hierarchical structure showing relationships"""
        output = []

        output.append("=" * 80)
        output.append("TYPE HIERARCHY AND RELATIONSHIPS")
        output.append("=" * 80)

        # Show unions with their resolved types
        if self.xml_export.unions:
            output.append("\n" + "=" * 80)
            output.append("UNIONS")
            output.append("=" * 80)

            for union in self.xml_export.unions:
                output.append(f"\n{union.name}:")

                for member in union.members:
                    type_info = self._get_type_info_string(member.type)
                    output.append(f"  {member.name}: {member.type} {type_info}")

        # Show structures with their resolved types
        if self.xml_export.structures:
            output.append("\n" + "=" * 80)
            output.append("STRUCTURES")
            output.append("=" * 80)

            for struct in self.xml_export.structures:
                output.append(f"\n{struct.name}:")

                for member in struct.members:
                    type_info = self._get_type_info_string(member.type)
                    output.append(f"  {member.name}: {member.type} {type_info}")

        # Show enums
        if self.xml_export.enums:
            output.append("\n" + "=" * 80)
            output.append("ENUMERATIONS")
            output.append("=" * 80)

            for enum in self.xml_export.enums:
                output.append(f"\n{enum.name} ({enum.base_type}):")

                for value in enum.values:
                    output.append(f"  {value.name} = {value.value}")

        # Show type dependencies
        output.append("\n" + "=" * 80)
        output.append("TYPE DEPENDENCIES")
        output.append("=" * 80)

        dependencies = self._build_dependency_graph()
        for type_name, depends_on in dependencies.items():
            if depends_on:
                output.append(f"\n{type_name} depends on:")
                for dep in depends_on:
                    output.append(f"  - {dep}")

        return "\n".join(output)

    def _get_type_info_string(self, type_name: str) -> str:
        """Get string representation of type information"""
        if type_name in self.type_registry:
            type_info = self.type_registry[type_name]

            if isinstance(type_info, EnumType):
                return f"[ENUM with {len(type_info.values)} values]"
            elif isinstance(type_info, StructureType):
                type_kind = "UNION" if type_info.is_union else "STRUCT"
                return f"[{type_kind} with {len(type_info.members)} members]"
            elif isinstance(type_info, DataType):
                return f"[BASIC TYPE: {type_info.base_type}]"

        return "[UNKNOWN TYPE]"

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph of types"""
        dependencies = {}

        # Add all types to the graph
        for type_name in self.type_registry.keys():
            dependencies[type_name] = []

        # Find dependencies for unions
        for union in self.xml_export.unions:
            for member in union.members:
                if member.type in self.type_registry and member.type != union.name:
                    dependencies[union.name].append(member.type)

        # Find dependencies for structures
        for struct in self.xml_export.structures:
            for member in struct.members:
                if member.type in self.type_registry and member.type != struct.name:
                    dependencies[struct.name].append(member.type)

        # Remove empty entries
        return {k: v for k, v in dependencies.items() if v}

    def export_detailed_type_info(self, type_name: str) -> Optional[str]:
        """Export detailed information about a specific type"""
        if type_name not in self.type_registry:
            return None

        type_info = self.type_registry[type_name]
        output = []

        output.append("=" * 80)
        output.append(f"DETAILED TYPE INFORMATION: {type_name}")
        output.append("=" * 80)

        if isinstance(type_info, EnumType):
            output.append(f"\nType: Enumeration")
            output.append(f"Base Type: {type_info.base_type}")
            output.append(f"Values ({len(type_info.values)}):")

            for value in type_info.values:
                desc = f" - {value.description}" if value.description else ""
                output.append(f"  {value.name} = {value.value}{desc}")

        elif isinstance(type_info, StructureType):
            type_kind = "Union" if type_info.is_union else "Structure"
            output.append(f"\nType: {type_kind}")
            output.append(f"Members ({len(type_info.members)}):")

            for member in type_info.members:
                init = f" = {member.initial_value}" if member.initial_value else ""

                # Get detailed info about the member type
                member_type_info = self._get_detailed_type_info(member.type)
                type_details = f"\n      Type details: {member_type_info}" if member_type_info else ""

                output.append(f"  {member.name}: {member.type}{init}{type_details}")

        elif isinstance(type_info, DataType):
            output.append(f"\nType: Basic Data Type")
            output.append(f"Base Type: {type_info.base_type}")
            if type_info.initial_value:
                output.append(f"Initial Value: {type_info.initial_value}")

        # Show where this type is used
        output.append("\n" + "-" * 40)
        output.append("USED IN:")

        used_in = self._find_where_type_is_used(type_name)
        if used_in:
            for usage in used_in:
                output.append(f"  - {usage}")
        else:
            output.append("  (Not referenced by other types)")

        return "\n".join(output)

    def _get_detailed_type_info(self, type_name: str) -> Optional[str]:
        """Get detailed information about a type"""
        if type_name not in self.type_registry:
            return None

        type_info = self.type_registry[type_name]

        if isinstance(type_info, EnumType):
            return f"Enumeration with {len(type_info.values)} values"
        elif isinstance(type_info, StructureType):
            kind = "Union" if type_info.is_union else "Structure"
            return f"{kind} with {len(type_info.members)} members"
        elif isinstance(type_info, DataType):
            return f"Basic type: {type_info.base_type}"

        return None

    def _find_where_type_is_used(self, type_name: str) -> List[str]:
        """Find where a type is used as a member"""
        used_in = []

        # Check unions
        for union in self.xml_export.unions:
            for member in union.members:
                if member.type == type_name and union.name != type_name:
                    used_in.append(f"Union: {union.name} (member: {member.name})")

        # Check structures
        for struct in self.xml_export.structures:
            for member in struct.members:
                if member.type == type_name and struct.name != type_name:
                    used_in.append(f"Structure: {struct.name} (member: {member.name})")

        # Check POUs
        for pou in self.xml_export.pous:
            for variable in pou.variables:
                if variable.type == type_name:
                    used_in.append(f"POU: {pou.name} (variable: {variable.name})")

        # Check global variables
        for global_var in self.xml_export.global_variables:
            if global_var.type == type_name:
                used_in.append(f"Global Variable: {global_var.name}")

        return used_in