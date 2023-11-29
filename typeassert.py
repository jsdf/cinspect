from typing import Any


def as_string(anything: Any) -> str:
    if isinstance(anything, str):
        return anything
    raise TypeError(f"Expected string, got {type(anything).__name__}")
