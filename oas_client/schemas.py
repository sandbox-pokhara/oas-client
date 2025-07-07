from pathlib import Path
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader

from oas_client.types import resolve_type


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


def render_schemas(spec: dict[str, Any], template_dir: Path) -> str:
    schemas, imports = find_schemas(spec)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=imports)
    return output_code
