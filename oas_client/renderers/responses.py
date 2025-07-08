from pathlib import Path
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader

from oas_client.parser import find_schemas


def render_responses(spec: dict[str, Any], template_dir: Path) -> str:
    schemas, imports = find_schemas(spec, partial=False)
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("schemas.jinja2")
    output_code = template.render(schemas=schemas, imports=imports)
    return output_code
