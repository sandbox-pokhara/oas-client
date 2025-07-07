from pathlib import Path
from typing import Any
from typing import Literal

from jinja2 import Environment
from jinja2 import FileSystemLoader

from oas_client.types import resolve_type
from oas_client.utils import to_pascal_case


def find_parameters(
    spec: dict[str, Any], in_filter: Literal["query", "path"]
) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:
    output: list[dict[str, Any]] = []
    imports: set[tuple[str, str]] = set()

    paths: dict[str, dict[str, dict[str, Any]]] = spec.get("paths", {})

    for _, methods in paths.items():
        for _, op in methods.items():
            operation_id = op.get("operationId")
            if not operation_id:
                continue

            params: list[dict[str, Any]] = [
                o for o in op.get("parameters", []) if o.get("in") == in_filter
            ]
            if not params:
                continue
            fields: list[dict[str, str]] = []
            for q in params:
                name = q["name"]
                required = q.get("required", False)
                schema = q.get("schema", {})
                type_str, imps = resolve_type(schema)
                if not required:
                    imports.add(("typing", "NotRequired"))
                    type_str = f"NotRequired[{type_str}]"
                fields.append({"name": name, "type": type_str})
                for i in imps:
                    imports.add(i)

            imports.add(("typing", "TypedDict"))
            output.append({"name": operation_id, "fields": fields})
    return output, imports


def render_queries(spec: dict[str, Any], template_dir: Path) -> str:
    schemas, imports = find_parameters(spec, in_filter="query")
    schemas = [
        {"name": to_pascal_case(s["name"] + "_query"), "fields": s["fields"]}
        for s in schemas
    ]
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=imports)
    return output_code


def render_params(spec: dict[str, Any], template_dir: Path) -> str:
    schemas, imports = find_parameters(spec, in_filter="path")
    schemas = [
        {"name": to_pascal_case(s["name"] + "_params"), "fields": s["fields"]}
        for s in schemas
    ]
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=imports)
    return output_code
