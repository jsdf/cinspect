# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false

from typing import Any
import clang.cindex


def as_string(anything: Any) -> str:
    if isinstance(anything, str):
        return anything
    raise TypeError(f"Expected string, got {type(anything).__name__}")


def as_cursor(anything: Any) -> clang.cindex.Cursor:
    if isinstance(anything, clang.cindex.Cursor):
        return anything
    raise TypeError(f"Expected clang.cindex.Cursor, got {type(anything).__name__}")


def as_type(anything: Any) -> clang.cindex.Type:
    if isinstance(anything, clang.cindex.Type):
        return anything
    raise TypeError(f"Expected clang.cindex.Type, got {type(anything).__name__}")


def as_location(anything: Any) -> clang.cindex.SourceLocation:
    if isinstance(anything, clang.cindex.SourceLocation):
        return anything
    raise TypeError(
        f"Expected clang.cindex.SourceLocation, got {type(anything).__name__}"
    )
