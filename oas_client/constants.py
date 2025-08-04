from typing import Literal

BASE_IMPORTS = set(
    [
        ("typing", "Any"),
        ("typing", "Literal"),
    ]
)
CONDITIONAL_IMPORTS: dict[Literal["pydantic", "typing"], set[tuple[str, str]]] = {
    "pydantic": set([("pydantic", "BaseModel")]),
    "typing": set([("typing", "TypedDict"), ("typing", "NotRequired")]),
}
