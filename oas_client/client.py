from pathlib import Path
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader

from oas_client.types import resolve_type


def render_client(spec: dict[str, Any], template_dir: Path) -> str:
    env = Environment(loader=FileSystemLoader(template_dir))
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

            # Extract query/path/header parameters
            parameters: list[dict[str, str]] = []
            queries: list[dict[str, str]] = []
            for param in op.get("parameters", []):
                name = param["name"]
                schema = param.get("schema", {})
                typ, _ = resolve_type(schema)
                if param["in"] == "path":
                    parameters.append({"name": name, "type": typ})
                if param["in"] == "query":
                    queries.append({"name": name, "type": typ})

            functions.append(
                {
                    "func_name": op_id,
                    "url": path,
                    "http_method": method,
                    "return": " | ".join(schemas),
                    "body": body,
                    "parameters": parameters,
                    "queries": queries,
                }
            )
    # NOTE: typed parameter and queries are not implemented yet
    return template.render(functions=functions)
