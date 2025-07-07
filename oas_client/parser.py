import argparse
import json
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


def load_schemas(
    openapi_path: str,
) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:
    with open(openapi_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

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


def render_typeddicts(
    schemas: list[dict[str, Any]],
    imports: set[tuple[str, str]],
    template_path: Path,
) -> str:
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template("typeddict.jinja2")
    return template.render(schemas=schemas, imports=imports)


def main(
    openapi_path: str,
    output_path: str,
    template_dir: Path = BASE_DIR / "templates",
):
    schemas, imports = load_schemas(openapi_path)
    output_code = render_typeddicts(schemas, imports, template_dir)
    output_code = isort.code(output_code)
    mode = black.Mode()
    output_code = black.format_str(output_code, mode=mode)
    Path(output_path).write_text(output_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI client from an OpenAPI JSON spec."
    )
    parser.add_argument("openapi_json", help="Path to the OpenAPI JSON file.")
    parser.add_argument("output_py", help="Path to the output Python file.")
    args = parser.parse_args()
    main(args.openapi_json, args.output_py)
