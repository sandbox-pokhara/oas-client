from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from oas_client.openapi import OpenAPI
from oas_client.parser import find_schemas, traverse_path_methods_get
from oas_client.types import ParserOutput
from oas_client.utils import render_imports


def render_responses(
    spec: OpenAPI,
    template_dir: Path,
    imports: set[tuple[str, str]],
    schema_cls_type: str,
) -> str:
    schemas = find_schemas(spec, partial=False, schema_cls_type=schema_cls_type)
    # render necessary schemas only
    response_schemas = traverse_path_methods_get(spec, "response")
    schemas_new: list[ParserOutput] = []
    for s in schemas:
        if s.name not in response_schemas:
            continue
        fields: list[Any] = []
        for field in s.fields:
            if isinstance(field, dict) and "value" in field:
                field.pop("value")
            fields.append(field)
        s.fields = fields
        schemas_new.append(s)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas_new, imports=render_imports(imports))
    return output_code
