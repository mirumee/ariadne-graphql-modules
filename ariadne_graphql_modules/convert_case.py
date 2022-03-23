from typing import Dict, Optional, Union, cast

from ariadne import convert_camel_case_to_snake
from graphql import DefinitionNode

from .types import FieldsDict

Overrides = Dict[str, str]
ArgsOverrides = Dict[str, Overrides]


def convert_case(
    overrides_or_fields: Optional[Union[FieldsDict, dict]] = None,
    map_fields_args=False,
):
    no_args_call = convert_case_call_without_args(overrides_or_fields)

    overrides = {}
    if not no_args_call:
        overrides = cast(dict, overrides_or_fields)

    def create_case_mappings(fields: FieldsDict, map_fields_args=False):
        if map_fields_args:
            return convert_args_cas(fields, overrides)

        return convert_aliases_case(fields, overrides)

    if no_args_call:
        fields = cast(FieldsDict, overrides_or_fields)
        return create_case_mappings(fields, map_fields_args)

    return create_case_mappings


def convert_case_call_without_args(
    overrides_or_fields: Optional[Union[FieldsDict, dict]] = None
) -> bool:
    if overrides_or_fields is None:
        return True

    if isinstance(list(overrides_or_fields.values())[0], DefinitionNode):
        return True

    return False


def convert_aliases_case(fields: FieldsDict, overrides: Overrides) -> Overrides:
    final_mappings = {}
    for field_name in fields:
        if field_name in overrides:
            field_name_final = overrides[field_name]
        else:
            field_name_final = convert_camel_case_to_snake(field_name)
        if field_name != field_name_final:
            final_mappings[field_name] = field_name_final
    return final_mappings


def convert_args_cas(fields: FieldsDict, overrides: ArgsOverrides) -> ArgsOverrides:
    final_mappings = {}
    for field_name, field_def in fields.items():
        arg_overrides: Overrides = overrides.get(field_name, {})
        arg_mappings = {}
        for arg in field_def.arguments:
            arg_name = arg.name.value
            if arg_name in arg_overrides:
                arg_name_final = arg_overrides[arg_name]
            else:
                arg_name_final = convert_camel_case_to_snake(arg_name)
            if arg_name != arg_name_final:
                arg_mappings[arg_name] = arg_name_final
        if arg_mappings:
            final_mappings[field_name] = arg_mappings
    return final_mappings
