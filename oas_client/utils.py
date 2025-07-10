from collections import defaultdict


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
