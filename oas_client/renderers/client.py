from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from oas_client.openapi import OpenAPI
from oas_client.parser import find_functions


def render_client(spec: OpenAPI, template_dir: Path, model_to_use: str) -> str:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("client.jinja2")
    functions = find_functions(spec)

    return template.render(functions=functions, model_used=model_to_use)
