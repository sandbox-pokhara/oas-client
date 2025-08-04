from warnings import warn

from pydantic import BaseModel

from oas_client.openapi import Reference, Schema


class ParserOutput(BaseModel):
    name: str
    fields: list[dict[str, str]] | list[str]
    type: str


class FunctionSignature(BaseModel):
    func_name: str
    url: str
    http_method: str
    return_: str
    body: str | None
    params: str | None
    query: str | None


def resolve_type(prop: Reference | Schema | None) -> str:
    """
    Returns type of the property and additional imports required
    """
    if prop is None:
        return "None"
    if isinstance(prop, Reference):
        schema_name = prop.ref.split("/")[-1]
        return f'"{schema_name}"'
    any_of: list[Reference | Schema] = prop.any_of
    if any_of:
        types: list[str] = []
        for p in any_of:
            t = resolve_type(p)
            types.append(t)
        temp_type = " | ".join(types)
        if '"' in temp_type:
            # remove the double quotes from the
            # schemas names, and extend it to whole type
            # for example:
            # t : "Atype" | None
            # 1. t -> Atype | None : by .replace
            # 2. t -> "Atype | None" : by .__repr__

            temp_type = temp_type.replace('"', "").__repr__()
        return temp_type
    t: str | None = prop.type
    if t == "string":
        return "str"
    elif t == "integer":
        return "int"
    elif t == "number":
        return "float"
    elif t == "boolean":
        return "bool"
    elif t == "null":
        return "None"
    elif t == "array":
        item_type = resolve_type(prop.items)
        return f"list[{item_type}]"
    elif t == "object":
        return "dict[str, Any]"
    warn(f"Fallback to Any type for type:{t}")
    return "Any"
