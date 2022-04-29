from typing import Dict, Iterable, List, Tuple, Type, cast

from ariadne import (
    SchemaDirectiveVisitor,
    set_default_enum_values_on_schema,
    validate_schema_enum_values,
)
from graphql import (
    ConstDirectiveNode,
    DocumentNode,
    FieldDefinitionNode,
    GraphQLSchema,
    NamedTypeNode,
    ObjectTypeDefinitionNode,
    assert_valid_schema,
    build_ast_schema,
    concat_ast,
    parse,
)
from graphql.language import ast

from .bases import BaseType, BindableType, DeferredType, DefinitionType
from .enum_type import EnumType

ROOT_TYPES = ["Query", "Mutation", "Subscription"]


def make_executable_schema(
    *types,
    merge_roots: bool = True,
):
    all_types = get_all_types(types)

    type_defs: List[Type[DefinitionType]] = []
    for type_ in all_types:
        if issubclass(type_, DefinitionType):
            type_defs.append(type_)

    validate_no_missing_definitions(all_types, type_defs)

    schema = build_schema(type_defs, merge_roots)
    set_default_enum_values_on_schema(schema)
    assert_valid_schema(schema)
    validate_schema_enum_values(schema)
    repair_default_enum_values(schema, type_defs)

    add_directives_to_schema(schema, type_defs)

    return schema


def get_all_types(types: Iterable[Type[BaseType]]) -> List[Type[BaseType]]:
    all_types: List[Type[BaseType]] = []
    for leaf_type in types:
        for child_type in leaf_type.__get_types__():
            if child_type not in all_types:
                all_types.append(child_type)
    return all_types


def validate_no_missing_definitions(
    all_types: List[Type[BaseType]],
    type_defs: List[Type[DefinitionType]],
):
    deferred_names: List[str] = []
    for type_ in all_types:
        if isinstance(type_, DeferredType):
            deferred_names.append(type_.graphql_name)

    real_names = [type_.graphql_name for type_ in type_defs]
    missing_names = set(deferred_names) - set(real_names)
    if missing_names:
        raise ValueError(
            "Following types are defined as deferred and are missing "
            f"from schema: {', '.join(missing_names)}"
        )


def build_schema(
    type_defs: List[Type[DefinitionType]], merge_roots: bool = True
) -> GraphQLSchema:
    schema_definitions: List[ast.DocumentNode] = []
    if merge_roots:
        schema_definitions.append(build_root_schema(type_defs))
        for type_ in type_defs:
            if type_.graphql_name not in ROOT_TYPES or not merge_roots:
                schema_definitions.append(parse(type_.__schema__))

    ast_document = concat_ast(schema_definitions)
    schema = build_ast_schema(ast_document)

    for type_ in type_defs:
        if issubclass(type_, BindableType):
            type_.__bind_to_schema__(schema)

    return schema


def build_root_schema(type_defs: List[Type[DefinitionType]]) -> DocumentNode:
    root_types: Dict[str, List[Type[DefinitionType]]] = {
        "Query": [],
        "Mutation": [],
        "Subscription": [],
    }

    for type_def in type_defs:
        if type_def.graphql_name in root_types:
            root_types[type_def.graphql_name].append(type_def)

    schema: List[DocumentNode] = []
    for root_type_defs in root_types.values():
        if len(root_type_defs) == 1:
            schema.append(parse(root_type_defs[0].__schema__))
        elif root_type_defs:
            schema.append(merge_root_types(root_type_defs))

    return concat_ast(schema)


def merge_root_types(type_defs: List[Type[DefinitionType]]) -> DocumentNode:
    interfaces: List[NamedTypeNode] = []
    directives: List[ConstDirectiveNode] = []
    fields: Dict[str, Tuple[FieldDefinitionNode, Type[DefinitionType]]] = {}

    for type_ in type_defs:
        type_definition = cast(
            ObjectTypeDefinitionNode,
            parse(type_.__schema__).definitions[0],
        )
        interfaces.extend(type_definition.interfaces)
        directives.extend(type_definition.directives)

        for field_def in type_definition.fields:
            field_name = field_def.name.value
            if field_name in fields:
                other_type_name = fields[field_name][1].__name__
                raise ValueError(
                    f"Multiple {type_.graphql_name} types are defining same field "
                    f"'{field_name}': {other_type_name}, {type_.__name__}"
                )

            fields[field_name] = (field_def, type_)

    merged_definition = ast.ObjectTypeDefinitionNode()
    merged_definition.name = ast.NameNode()
    merged_definition.name.value = type_defs[0].graphql_name
    merged_definition.interfaces = tuple(interfaces)
    merged_definition.directives = tuple(directives)
    merged_definition.fields = tuple(
        fields[field_name][0] for field_name in sorted(fields)
    )

    merged_document = DocumentNode()
    merged_document.definitions = (merged_definition,)

    return merged_document


def add_directives_to_schema(
    schema: GraphQLSchema, type_defs: List[Type[DefinitionType]]
):
    directives: Dict[str, Type[SchemaDirectiveVisitor]] = {}
    for type_def in type_defs:
        visitor = getattr(type_def, "__visitor__", None)
        if visitor and issubclass(visitor, SchemaDirectiveVisitor):
            directives[type_def.graphql_name] = visitor

    if directives:
        SchemaDirectiveVisitor.visit_schema_directives(schema, directives)


def repair_default_enum_values(schema, types_list: List[Type[DefinitionType]]) -> None:
    for type_ in types_list:
        if issubclass(type_, EnumType):
            type_.__bind_to_default_values__(schema)
