from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from oas_client.parser import find_functions


def render_client(spec: dict[str, Any], template_dir: Path) -> str:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("client.jinja2")
    functions = find_functions(spec)
    return template.render(functions=functions)
