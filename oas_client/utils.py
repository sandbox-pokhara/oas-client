from collections import defaultdict

from oas_client.exceptions import ReferenceNotResolved
from oas_client.openapitype import Components, Reference, Response, Schema


def to_pascal_case(s: str) -> str:
    parts = s.split("_")
    return "".join(p[0].upper() + p[1:] if p else p for p in parts)


def render_imports(imports: set[tuple[str, str]]):
    """
    Groups and sorts imports and prints Python import statements.
    Each import is a tuple of (module, item), e.g. ("os", "path"), ("os", "mkdir").

    Prints:
        Statements like: from module import item1, item2
    """
    grouped = defaultdict[str, list[str]](list)

    for module, item in imports:
        grouped[module].append(item)

    output: list[str] = []
    for module in sorted(grouped):
        items = sorted(grouped[module])
        output.append(f"from {module} import {', '.join(items)}")

    return "\n".join(output)


def get_schema_by_reference(component: Components, ref: Reference) -> Schema:
    # pattren = #/components/schemas/PagedServerSchema
    schema_name = ref.ref.split("/")[-1]
    schema = component.schemas.get(schema_name, None)
    if isinstance(schema, Schema):
        return schema
    raise ReferenceNotResolved(f"Could not find matching schema for Reference:{ref}")


def get_response_by_refrenece(component: Components, ref: Reference) -> Response:
    # pattren = #/components/schemas/PagedServerSchema
    response_name = ref.ref.split("/")[-1]
    response = component.schemas.get(response_name, None)
    if isinstance(response, Response):
        return response
    raise ReferenceNotResolved(f"Could not find matching schema for Reference:{ref}")
