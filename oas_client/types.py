from warnings import warn

from pydantic import BaseModel

from oas_client.openapi import Reference, Schema


class ParserOutput(BaseModel):
    name: str
    fields: list[dict[str, str]]
    type: str


def resolve_type(prop: Reference | Schema | None) -> tuple[str, list[tuple[str, str]]]:
    """
    Returns type of the property and additional imports required
    """
    if prop is None:
        return "None", []
    if isinstance(prop, Reference):
        schema_name = prop.ref.split("/")[-1]
        return f'"{schema_name}"', []
    any_of: list[Reference | Schema] = prop.any_of
    if any_of:
        types: list[str] = []
        imports: list[tuple[str, str]] = []
        for p in any_of:
            t, i = resolve_type(p)
            types.append(t)
            imports += i
        return " | ".join(types), imports
    t: str | None = prop.type
    if t == "string":
        return "str", []
    elif t == "integer":
        return "int", []
    elif t == "number":
        return "float", []
    elif t == "boolean":
        return "bool", []
    elif t == "null":
        return "None", []
    elif t == "array":
        item_type, imports = resolve_type(prop.items)
        return f"list[{item_type}]", imports
    elif t == "object":
        return "dict[str, Any]", [("typing", "Any")]
    warn(f"Fallback to Any type for type:{t}")
    return "Any", [("typing", "Any")]
