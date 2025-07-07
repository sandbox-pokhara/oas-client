from pathlib import Path
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader

from oas_client.utils import to_pascal_case


def render_client(spec: dict[str, Any], template_dir: Path) -> str:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("client.jinja2")

    paths: dict[str, dict[str, dict[str, Any]]] = spec.get("paths", {})
    functions: list[dict[str, Any]] = []

    for path, methods in paths.items():
        for method, op in methods.items():
            op_id = op["operationId"]

            # Extract response schemas
            schemas: list[str] = []
            responses: dict[str, dict[str, Any]] = op.get("responses", {})
            for _, res in responses.items():
                if "application/json" in res.get("content", {}):
                    schema_ref = res["content"]["application/json"]["schema"][
                        "$ref"
                    ]
                    schemas.append("responses." + schema_ref.split("/")[-1])

            # Extract request body schema
            body = None
            if "requestBody" in op:
                content = op["requestBody"].get("content", {})
                if "application/json" in content:
                    schema_ref = content["application/json"]["schema"]["$ref"]
                    body = "requests." + schema_ref.split("/")[-1]

            # Extract query/path parameters exists
            is_params = [
                p for p in op.get("parameters", []) if p["in"] == "path"
            ] != []
            is_query = [
                p for p in op.get("parameters", []) if p["in"] == "query"
            ] != []

            functions.append(
                {
                    "func_name": op_id,
                    "url": path,
                    "http_method": method,
                    "return": " | ".join(schemas),
                    "body": body,
                    "params": (
                        "params." + to_pascal_case(op_id + "_params")
                        if is_params
                        else None
                    ),
                    "query": (
                        "queries." + to_pascal_case(op_id + "_query")
                        if is_query
                        else None
                    ),
                }
            )
    return template.render(functions=functions)
