from typing import Any, Literal

from oas_client.types import resolve_type
from oas_client.utils import to_pascal_case


def find_schemas(
    spec: dict[str, Any], partial: bool = False
) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:
    schemas: dict[str, dict[str, Any]] = spec.get("components", {}).get("schemas", {})
    output: list[dict[str, Any]] = []
    imports: set[tuple[str, str]] = set()
    for name, schema in schemas.items():
        schema_type = schema.get("type")
        if schema_type == "object":
            imports.add(("typing_extensions", "TypedDict"))
            required: set[str] = set(schema.get("required", []))
            props: dict[str, dict[str, Any]] = schema.get("properties", {})
            fields: list[dict[str, str]] = []
            for prop_name, prop in props.items():
                type_str, imps = resolve_type(prop)
                if partial and prop_name not in required:
                    imports.add(("typing", "NotRequired"))
                    type_str = f"NotRequired[{type_str}]"
                fields.append({"name": prop_name, "type": type_str})
                for i in imps:
                    imports.add(i)
            output.append({"name": name, "fields": fields, "type": "TypedDict"})
        elif schema_type == "string":
            # assumes that all string schema has enum field
            # if string schema does not enum it will raise KeyError
            imports.add(("typing", "Literal"))
            output.append({"name": name, "fields": schema["enum"], "type": "Literal"})
        else:
            raise NotImplementedError(
                f"Schema type {schema_type} is not implemented. Create an"
                " issue in GitHub."
            )
    return output, imports


def find_parameters(
    spec: dict[str, Any], in_filter: Literal["query", "path"]
) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:
    output: list[dict[str, Any]] = []
    imports: set[tuple[str, str]] = set()

    paths: dict[str, dict[str, dict[str, Any]]] = spec.get("paths", {})

    for _, methods in paths.items():
        for _, op in methods.items():
            operation_id = op.get("operationId")
            if not operation_id:
                continue

            params: list[dict[str, Any]] = [
                o for o in op.get("parameters", []) if o.get("in") == in_filter
            ]
            if not params:
                continue
            fields: list[dict[str, str]] = []
            for q in params:
                name = q["name"]
                required = q.get("required", False)
                schema = q.get("schema", {})
                type_str, imps = resolve_type(schema)
                if not required:
                    imports.add(("typing", "NotRequired"))
                    type_str = f"NotRequired[{type_str}]"
                fields.append({"name": name, "type": type_str})
                for i in imps:
                    imports.add(i)

            imports.add(("typing_extensions", "TypedDict"))
            output.append({"name": operation_id, "fields": fields, "type": "TypedDict"})
    return output, imports


def find_functions(spec: dict[str, Any]):
    paths: dict[str, dict[str, dict[str, Any]]] = spec.get("paths", {})
    functions: list[dict[str, Any]] = []

    for path, methods in paths.items():
        for method, op in methods.items():
            op_id = op["operationId"]

            # Extract response schemas
            schemas: set[str] = set()
            responses: dict[str, dict[str, Any]] = op.get("responses", {})
            for code, res in responses.items():
                # only collect schemas with ok status because
                # exception is raised on non ok status by
                # res.raise_for_status in client methods
                if 200 <= int(code) <= 299 and "application/json" in res.get(
                    "content", {}
                ):
                    try:
                        schema_ref = res["content"]["application/json"]["schema"][
                            "$ref"
                        ]
                        schemas.add("responses." + schema_ref.split("/")[-1])
                    except KeyError:
                        # TODO: support non $ref schemas
                        schemas.add("Any")

            # Extract request body schema
            body = None
            if "requestBody" in op:
                content = op["requestBody"].get("content", {})
                if "application/json" in content:
                    try:
                        schema_ref = content["application/json"]["schema"]["$ref"]
                        body = "requests." + schema_ref.split("/")[-1]
                    except KeyError:
                        # TODO: support non $ref schemas
                        body = "Any"

            # Extract query/path parameters exists
            is_params = [p for p in op.get("parameters", []) if p["in"] == "path"] != []
            is_query = [p for p in op.get("parameters", []) if p["in"] == "query"] != []

            functions.append(
                {
                    "func_name": op_id,
                    "url": path,
                    "http_method": method,
                    "return": " | ".join(schemas) if schemas else "Any",
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
    return functions


def find_nested_schemas(spec: dict[str, Any], schema_ref: str) -> list[str]:
    schemas: dict[str, dict[str, Any]] = spec.get("components", {}).get("schemas", {})
    for name, s in schemas.items():
        if name != schema_ref.split("/")[-1]:
            continue
        props: dict[str, dict[str, Any]] = s.get("properties", {})
        for _, prop in props.items():
            if "anyOf" in prop:
                nested_list: list[str] = []
                for p in prop["anyOf"]:
                    if "$ref" in p:
                        nested_list += [p["$ref"]] + find_nested_schemas(
                            spec, p["$ref"]
                        )
                return nested_list
            if "items" in prop and "$ref" in prop["items"]:
                nested = prop["items"]["$ref"]
                return [nested] + find_nested_schemas(spec, nested)
            if "$ref" in prop:
                nested = prop["$ref"]
                return [nested] + find_nested_schemas(spec, nested)
    return []


def find_request_schemas(spec: dict[str, Any]):
    output: set[str] = set()
    paths: dict[str, dict[str, dict[str, Any]]] = spec.get("paths", {})
    for _, methods in paths.items():
        for _, op in methods.items():
            if "requestBody" in op:
                content = op["requestBody"].get("content", {})
                if "application/json" in content:
                    try:
                        schema_ref = content["application/json"]["schema"]["$ref"]
                        output.add(schema_ref.split("/")[-1])
                        for n in find_nested_schemas(spec, schema_ref):
                            output.add(n.split("/")[-1])
                    except KeyError:
                        pass
    return list(output)


def find_response_schemas(spec: dict[str, Any]):
    output: set[str] = set()
    paths: dict[str, dict[str, dict[str, Any]]] = spec.get("paths", {})
    for _, methods in paths.items():
        for _, op in methods.items():
            responses: dict[str, dict[str, Any]] = op.get("responses", {})
            for _, res in responses.items():
                try:
                    schema_ref: str = res["content"]["application/json"]["schema"][
                        "$ref"
                    ]
                    schema = schema_ref.split("/")[-1]
                    output.add(schema)
                    for n in find_nested_schemas(spec, schema_ref):
                        output.add(n.split("/")[-1])
                except KeyError:
                    pass
    return list(output)
