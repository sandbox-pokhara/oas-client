from typing import Literal
from warnings import warn

from oas_client.openapi import (
    OpenAPI,
    Operation,
    Parameter,
    Reference,
    RequestBody,
    Schema,
)
from oas_client.types import FunctionSignature, ParserOutput, resolve_type
from oas_client.utils import (
    get_response_by_reference,
    get_schema_by_reference,
    to_pascal_case,
)


def find_schemas(
    spec: OpenAPI, schema_cls_type: str, partial: bool = False
) -> list[ParserOutput]:
    if not spec.components:
        return []
    schemas = spec.components.schemas
    output: list[ParserOutput] = []
    for name, schema in schemas.items():
        if isinstance(schema, Reference):
            schema = get_schema_by_reference(spec.components, schema)
        schema_type = schema.type
        if schema_type == "object":
            fields: list[dict[str, str]] = []
            required: set[str] = set(schema.required)
            props = schema.properties
            for prop_name, prop in props.items():
                type_str = resolve_type(prop)
                field = {"name": prop_name}
                if partial and prop_name not in required:
                    if schema_cls_type == "BaseModel":
                        field["value"] = "None"
                        if not type_str.endswith("| None"):
                            type_str = f"{type_str} | None"
                    else:
                        type_str = f"NotRequired[{type_str}]"

                field["type"] = type_str
                fields.append(field)

            output.append(ParserOutput(name=name, fields=fields, type=schema_cls_type))
        elif schema_type == "string":
            output.append(ParserOutput(name=name, fields=schema.enum, type="Literal"))
        else:
            raise NotImplementedError(
                f"Schema type {schema_type} is not implemented. Create an"
                " issue in GitHub."
            )
    return output


def find_parameters(
    spec: OpenAPI, in_filter: Literal["query", "path"], parameter_cls_type: str
) -> list[ParserOutput]:
    output: list[ParserOutput] = []

    for _, path_item in spec.paths.items():
        operations = [
            path_item.get,
            path_item.put,
            path_item.post,
            path_item.delete,
            path_item.options,
            path_item.head,
            path_item.patch,
            path_item.trace,
        ]

        for operation in operations:
            if operation is None:
                continue
            operation_id = operation.operation_id
            if not operation_id:
                continue

            params = [
                o
                for o in operation.parameters
                if isinstance(o, Parameter) and o.in_.value == in_filter
            ]
            if not params:
                continue
            fields: list[dict[str, str]] = []
            for q in params:
                name = q.name
                required = q.required
                schema = q.schema_
                type_str = resolve_type(schema)
                if not required:
                    if not type_str.endswith("| None"):
                        type_str = f"{type_str} | None"
                fields.append({"name": name, "type": type_str})

            output.append(
                ParserOutput(
                    name=operation_id,
                    fields=fields,
                    type=parameter_cls_type,
                )
            )

    return output


def find_functions(spec: OpenAPI):
    functions: list[FunctionSignature] = []

    for path, path_item in spec.paths.items():
        operations = [
            ("get", path_item.get),
            ("put", path_item.put),
            ("post", path_item.post),
            ("delete", path_item.delete),
            ("options", path_item.options),
            ("head", path_item.head),
            ("patch", path_item.patch),
            ("trace", path_item.trace),
        ]

        for method, op in operations:
            if op is None or op.operation_id is None:
                continue
            op_id = op.operation_id

            # Extract response schemas
            schemas: set[str] = set()
            responses = op.responses
            for code, res in responses.items():
                # only collect schemas with ok status because
                # exception is raised on non ok status by
                # res.raise_for_status in client methods
                if isinstance(res, Reference):
                    schemas.add(res.ref.split("/")[-1])
                    continue
                if 200 <= int(code) <= 299 and "application/json" in res.content:
                    _type = res.content["application/json"].schema_
                    if isinstance(_type, Reference):
                        schemas.add("responses." + _type.ref.split("/")[-1])
                    elif _type is None:
                        schemas.add("None")
                    else:
                        _type = _type.items
                        match _type:
                            case None:
                                schemas.add("None")
                            case Reference():
                                schemas.add("responses." + _type.ref.split("/")[-1])
                            case Schema():
                                warn(
                                    f"Direct schema is not handled in find_functions. Falling back to Any for type:{_type}"
                                )
                                schemas.add("Any")
            # Extract request body schema
            body = None
            if op.request_body and isinstance(op.request_body, RequestBody):
                content = op.request_body.content
                if "application/json" in content:
                    _type = content["application/json"].schema_
                    if isinstance(_type, Reference):
                        body = "requests." + _type.ref.split("/")[-1]
                    elif _type is not None:
                        warn(
                            f"Direct schema is not handled in find_functions. Falling back to Any for type:{_type}"
                        )
                        body = "Any"

            # Extract query/path parameters exists
            is_params = [
                p
                for p in op.parameters
                if isinstance(p, Parameter) and p.in_.value == "path"
            ]
            is_query = [
                p
                for p in op.parameters
                if isinstance(p, Parameter) and p.in_.value == "query"
            ] != []

            functions.append(
                FunctionSignature(
                    func_name=op_id,
                    url=path,
                    http_method=method,
                    return_=" | ".join(schemas) if schemas else "Any",
                    body=body,
                    params=(
                        "params." + to_pascal_case(str(op_id) + "_params")
                        if is_params
                        else None
                    ),
                    query=(
                        "queries." + to_pascal_case(str(op_id) + "_query")
                        if is_query
                        else None
                    ),
                )
            )
    return functions


def request_schemas_parser(spec: OpenAPI, operation: Operation) -> list[str]:
    if operation.request_body is None:
        return []

    if isinstance(operation.request_body, Reference):
        return [operation.request_body.ref.split("/")[-1]]

    content = operation.request_body.content
    schemas_list: list[str] = []
    if "application/json" in content:
        _type = content["application/json"].schema_
        if isinstance(_type, Reference):
            schemas_list.append(_type.ref.split("/")[-1])
            for n in find_nested_schemas(spec, _type.ref):
                schemas_list.append(n.split("/")[-1])
            return schemas_list
        elif _type is None:
            return schemas_list
        warn(
            "Direct schema is not handled in request schemas parser. Falling back to Any"
        )
        return ["Any"]
    return schemas_list


def response_schemas_parser(spec: OpenAPI, operation: Operation) -> list[str]:
    output: list[str] = []
    for _, response in operation.responses.items():
        # Handle Reference objects
        if isinstance(response, Reference):
            if spec.components is None:
                continue
            response = get_response_by_reference(spec.components, response)

        # Look for application/json content
        json_content = response.content.get("application/json")
        if json_content is None:
            continue

        if json_content.schema_ is None:
            continue

        # Handle schema references
        if isinstance(json_content.schema_, Reference):
            schema_ref = json_content.schema_.ref
            schema_name = schema_ref.split("/")[-1]
            output.append(schema_name)

            # Find nested schemas
            for nested_ref in find_nested_schemas(spec, schema_ref):
                nested_name = nested_ref.split("/")[-1]
                output.append(nested_name)

        # Handle schema schema
        if isinstance(json_content.schema_, Schema):
            itms = json_content.schema_.items
            match itms:
                case None:
                    continue
                case Reference():
                    schema_name = itms.ref.split("/")[-1]
                    output.append(schema_name)
                case Schema():
                    continue
    return output


def traverse_path_methods_get(
    spec: OpenAPI, parse: Literal["requests", "response"]
) -> list[str]:
    output: set[str] = set()
    if not spec.components:
        return []

    parse_callback = None
    match parse:
        case "requests":
            parse_callback = request_schemas_parser
        case "response":
            parse_callback = response_schemas_parser

    for _, path_item in spec.paths.items():
        operations = [
            path_item.get,
            path_item.put,
            path_item.post,
            path_item.delete,
            path_item.options,
            path_item.head,
            path_item.patch,
            path_item.trace,
        ]

        for operation in operations:
            if operation is None:
                continue
            output = output.union(set(parse_callback(spec, operation)))

    return list(output)


def find_nested_schemas(spec: OpenAPI, schema_ref: str) -> list[str]:
    nested_refs: set[str] = set()

    if spec.components is None:
        return list(nested_refs)

    # Extract schema name from reference
    schema_name = schema_ref.split("/")[-1]
    schema = spec.components.schemas.get(schema_name)

    if schema is None or isinstance(schema, Reference):
        return list(nested_refs)

    collect_schema_refs(schema, nested_refs)
    return list(nested_refs)


def collect_schema_refs(schema: Schema, refs: set[str]):
    if schema.properties:
        for prop_schema in schema.properties.values():
            if isinstance(prop_schema, Reference):
                refs.add(prop_schema.ref)
            else:
                collect_schema_refs(prop_schema, refs)

    if schema.items:
        if isinstance(schema.items, Reference):
            refs.add(schema.items.ref)
        else:
            collect_schema_refs(schema.items, refs)

    if isinstance(schema.additional_properties, Reference):
        refs.add(schema.additional_properties.ref)
    elif isinstance(schema.additional_properties, Schema):
        collect_schema_refs(schema.additional_properties, refs)

    for composition_list in [schema.all_of, schema.one_of, schema.any_of]:
        if composition_list:
            for item in composition_list:
                if isinstance(item, Reference):
                    refs.add(item.ref)
                else:
                    collect_schema_refs(item, refs)

    if schema.not_:
        if isinstance(schema.not_, Reference):
            refs.add(schema.not_.ref)
        else:
            collect_schema_refs(schema.not_, refs)
