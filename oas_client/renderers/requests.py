from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from oas_client.openapi import OpenAPI
from oas_client.parser import find_schemas, traverse_path_methods_get
from oas_client.utils import render_imports


def render_requests(
    spec: OpenAPI,
    template_dir: Path,
    imports: set[tuple[str, str]],
    schema_cls_type: str,
) -> str:
    schemas = find_schemas(spec, partial=True, schema_cls_type=schema_cls_type)
    # render necessary schemas only
    request_schemas = traverse_path_methods_get(spec, "requests")
    schemas = [s for s in schemas if s.name in request_schemas]
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=render_imports(imports))
    return output_code
