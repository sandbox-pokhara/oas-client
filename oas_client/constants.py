from typing import Literal

BASE_IMPORTS = {
    ("typing", "Any"),
    ("typing", "Literal"),
}
CONDITIONAL_IMPORTS: dict[Literal["pydantic", "typing"], set[tuple[str, str]]] = {
    "pydantic": {("pydantic", "BaseModel")},
    "typing": {("typing_extensions", "TypedDict"), ("typing", "NotRequired")},
}
