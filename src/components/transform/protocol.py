"""Transform component protocol."""

from typing import Any, Protocol


class TransformFn(Protocol):
    """A callable that transforms data, returning the transformed result."""

    def __call__(self, data: Any) -> Any: ...
