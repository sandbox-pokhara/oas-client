from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from oas_client.openapitype import OpenAPI
from oas_client.parser import find_schemas, traverse_path_methods_get
from oas_client.utils import render_imports


def render_responses(spec: OpenAPI, template_dir: Path) -> str:
    schemas, imports = find_schemas(spec, partial=False)
    # render necessary schemas only
    response_schemas = traverse_path_methods_get(spec, "response")
    schemas = [s for s in schemas if s.name in response_schemas]
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=render_imports(imports))
    return output_code
