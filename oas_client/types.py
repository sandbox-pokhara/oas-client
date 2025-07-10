from typing import Any


def resolve_type(prop: dict[str, Any]) -> tuple[str, list[tuple[str, str]]]:
    """
    Returns type of the property and additional imports required
    """
    if "$ref" in prop:
        schema = prop["$ref"].split("/")[-1]
        return f'"{schema}"', []

    any_of: list[dict[str, Any]] | None = prop.get("anyOf")
    if any_of is not None:
        types: list[str] = []
        imports: list[tuple[str, str]] = []
        for p in any_of:
            t, i = resolve_type(p)
            types.append(t)
            imports += i
        return " | ".join(types), imports
    t: str | None = prop.get("type")
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
        item_type, imports = resolve_type(prop.get("items", {}))
        return f"list[{item_type}]", imports
    elif t == "object":
        return "dict[str, Any]", [("typing", "Any")]
    return "Any", [("typing", "Any")]
