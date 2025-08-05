from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from oas_client.openapi import OpenAPI
from oas_client.parser import find_parameters
from oas_client.utils import render_imports, to_pascal_case


def render_params(
    spec: OpenAPI,
    template_dir: Path,
    imports: set[tuple[str, str]],
    parms_cls_type: str,
) -> str:
    schemas = find_parameters(spec, in_filter="path", parameter_cls_type=parms_cls_type)
    schemas = [
        s.model_copy(update={"name": to_pascal_case(s.name + "_params")})
        for s in schemas
    ]
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=render_imports(imports))
    return output_code
