"""Filter component protocol."""
from typing import Any, Protocol


class FilterFn(Protocol):
    """A callable that filters data, returning the filtered result."""

    def __call__(self, data: Any) -> Any: ...
