"""
Data models for Codesys XML exports
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


# 1. First define the Enum
class XmlExportType(Enum):
    """Types of XML exports"""
    UNKNOWN = "unknown"
    TYPE_B = "type_b"
    PROJECT = "project"
    LIBRARY = "library"
    APPLICATION = "application"


# 2. Define other enums
class PouType(Enum):
    """Types of POUs (Program Organization Units)"""
    FUNCTION = "function"
    FUNCTION_BLOCK = "function_block"
    PROGRAM = "program"


# 3. Define simple dataclasses
@dataclass
class EnumValue:
    """Enumeration value"""
    name: str
    value: str
    description: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'value': self.value,
            'description': self.description
        }


@dataclass
class EnumType:
    """Enumeration type"""
    name: str
    base_type: str = "INT"
    values: List[EnumValue] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'base_type': self.base_type,
            'values': [v.to_dict() for v in self.values]
        }


@dataclass
class DataTypeReference:
    """Reference to another data type"""
    name: str
    type_info: Optional[Any] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'type_info': str(self.type_info) if self.type_info else None
        }


class StructureMember:
    def __init__(self, name, type, description=None, initial_value=None):
        self.name = name
        self.type = type
        self.description = description
        self.initial_value = initial_value
        self.type_reference = None  # Add this line

    def resolve_type(self, type_registry: Dict[str, Any]) -> None:
        """Resolve type reference from registry"""
        if self.type in type_registry:
            self.type_reference = DataTypeReference(name=self.type, type_info=type_registry[self.type])

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'initial_value': self.initial_value
        }


@dataclass
class DataType:
    """Basic data type"""
    name: str
    base_type: str = "UNKNOWN"
    initial_value: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'base_type': self.base_type,
            'initial_value': self.initial_value
        }


@dataclass
class Variable:
    """Variable definition"""
    name: str
    type: str
    initial_value: Optional[str] = None
    type_reference: Optional[DataTypeReference] = None

    def resolve_type(self, type_registry: Dict[str, Any]) -> None:
        """Resolve type reference from registry"""
        if self.type in type_registry:
            self.type_reference = DataTypeReference(name=self.type, type_info=type_registry[self.type])

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'type': self.type,
            'initial_value': self.initial_value
        }


@dataclass
class GlobalVariable:
    """Global variable"""
    name: str
    type: str
    initial_value: Optional[str] = None
    type_reference: Optional[DataTypeReference] = None

    def resolve_type(self, type_registry: Dict[str, Any]) -> None:
        """Resolve type reference from registry"""
        if self.type in type_registry:
            self.type_reference = DataTypeReference(name=self.type, type_info=type_registry[self.type])

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'type': self.type,
            'initial_value': self.initial_value
        }


@dataclass
class Pou:
    """POU (Program Organization Unit)"""
    name: str
    pou_type: PouType
    return_type: str = "VOID"
    variables: List[Variable] = field(default_factory=list)
    implementation: Optional[str] = None

    def resolve_variable_types(self, type_registry: Dict[str, Any]) -> None:
        """Resolve type references for all variables in the POU"""
        for variable in self.variables:
            variable.resolve_type(type_registry)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'pou_type': self.pou_type.value,
            'return_type': self.return_type,
            'variables': [v.to_dict() for v in self.variables],
            'implementation': self.implementation
        }


class StructureType:
    def __init__(self, name: str, members: List['StructureMember'] = None,
                 parent_structure: Optional[str] = None, is_union: bool = False):
        self.name = name
        self.members = members or []
        self.parent_structure = parent_structure  # For nested structures
        self.is_union = is_union
        self.nested_structures = []  # List of nested StructureType objects
        self.resolved_members = []  # Members with fully resolved types

    def get_all_members(self) -> List['StructureMember']:
        """Get all members including those from nested structures"""
        all_members = list(self.members)
        for nested in self.nested_structures:
            all_members.extend(nested.get_all_members())
        return all_members

    def resolve_member_types(self, type_registry: Dict[str, Any]) -> None:
        """Resolve type references for all members in the structure"""
        for member in self.members:
            if hasattr(member, 'resolve_type'):
                member.resolve_type(type_registry)

        # Also resolve nested structures
        for nested_struct in self.nested_structures:
            nested_struct.resolve_member_types(type_registry)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'is_union': self.is_union,
            'members': [member.to_dict() for member in self.members],
            'nested_structures': [ns.to_dict() for ns in self.nested_structures],
            'parent_structure': self.parent_structure
        }


# 4. Finally define XmlExport which references XmlExportType
@dataclass
class XmlExport:
    """Complete XML export structure"""
    export_type: XmlExportType  # Now XmlExportType is defined above
    file_path: str
    data_types: List[DataType] = field(default_factory=list)
    enums: List[EnumType] = field(default_factory=list)
    structures: List[StructureType] = field(default_factory=list)
    unions: List[StructureType] = field(default_factory=list)
    pous: List[Pou] = field(default_factory=list)
    global_variables: List[GlobalVariable] = field(default_factory=list)

    def get_summary(self) -> Dict[str, int]:
        """Get summary of parsed items"""
        return {
            'total_items': len(self.data_types) + len(self.enums) + len(self.structures) +
                           len(self.unions) + len(self.pous) + len(self.global_variables),
            'data_types': len(self.data_types),
            'enums': len(self.enums),
            'structures': len(self.structures),
            'unions': len(self.unions),
            'pous': len(self.pous),
            'global_variables': len(self.global_variables)
        }

    def get_all_types(self) -> Dict[str, Any]:
        """Get all types in a single registry"""
        type_registry = {}

        # Add enums
        for enum in self.enums:
            type_registry[enum.name] = enum

        # Add structures
        for struct in self.structures:
            type_registry[struct.name] = struct

        # Add unions
        for union in self.unions:
            type_registry[union.name] = union

        # Add basic data types
        for data_type in self.data_types:
            type_registry[data_type.name] = data_type

        return type_registry

    def resolve_all_type_references(self) -> None:
        """Resolve all type references in the export"""
        type_registry = self.get_all_types()

        # Resolve structure member types
        for struct in self.structures:
            struct.resolve_member_types(type_registry)

        # Resolve union member types
        for union in self.unions:
            union.resolve_member_types(type_registry)

        # Resolve POU variable types
        for pou in self.pous:
            pou.resolve_variable_types(type_registry)

        # Resolve global variable types
        for global_var in self.global_variables:
            global_var.resolve_type(type_registry)

    def to_dict(self):
        """Convert XmlExport object to dictionary format for ExportManager"""
        return {
            'unions': [u.to_dict() for u in self.unions],
            'enums': [e.to_dict() for e in self.enums],
            'structures': [s.to_dict() for s in self.structures],
            'data_types': [d.to_dict() for d in self.data_types],
            'pous': [p.to_dict() for p in self.pous],
            'global_variables': [g.to_dict() for g in self.global_variables]
        }