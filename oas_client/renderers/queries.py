from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from oas_client.parser import find_parameters
from oas_client.utils import render_imports, to_pascal_case


def render_queries(spec: dict[str, Any], template_dir: Path) -> str:
    schemas, imports = find_parameters(spec, in_filter="query")
    schemas = [
        {
            "name": to_pascal_case(s["name"] + "_query"),
            "fields": s["fields"],
            "type": s["type"],
        }
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
