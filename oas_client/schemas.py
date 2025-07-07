from pathlib import Path
from typing import Any

import black
import isort
from jinja2 import Environment
from jinja2 import FileSystemLoader

BASE_DIR = Path(__file__).parent


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
    t = prop.get("type")
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


def find_schemas(
    spec: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:

    schemas: dict[str, dict[str, Any]] = spec.get("components", {}).get(
        "schemas", {}
    )
    output: list[dict[str, Any]] = []
    imports: set[tuple[str, str]] = set()
    for name, schema in schemas.items():
        imports.add(("typing", "TypedDict"))
        required: set[str] = set(schema.get("required", []))
        props: dict[str, dict[str, Any]] = schema.get("properties", {})

        fields: list[dict[str, str]] = []
        for prop_name, prop in props.items():
            type_str, imps = resolve_type(prop)
            if prop_name not in required:
                imports.add(("typing", "NotRequired"))
                type_str = f"NotRequired[{type_str}]"
            fields.append({"name": prop_name, "type": type_str})
            for i in imps:
                imports.add(i)
        output.append({"name": name, "fields": fields})
    return output, imports


def render_schemas(spec: dict[str, Any]) -> str:
    schemas, imports = find_schemas(spec)
    env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=imports)
    output_code = isort.code(output_code)
    mode = black.Mode()
    output_code = black.format_str(output_code, mode=mode)
    return output_code
