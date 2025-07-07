def to_pascal_case(s: str) -> str:
    parts = s.split("_")
    return "".join(p[0].upper() + p[1:] if p else p for p in parts)
