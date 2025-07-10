from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from oas_client.parser import find_request_schemas, find_schemas
from oas_client.utils import render_imports


def render_requests(spec: dict[str, Any], template_dir: Path) -> str:
    schemas, imports = find_schemas(spec, partial=True)
    # render necessary schemas only
    schemas = [s for s in schemas if s["name"] in find_request_schemas(spec)]
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=render_imports(imports))
    return output_code
