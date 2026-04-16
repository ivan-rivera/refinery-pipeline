"""Filter component.

Usage:
    from src.components.filter import filter as apply_filter
    result = apply_filter(data)                    # uses _DEFAULT
    result = apply_filter(data, fns=[my_filter])   # custom sequence
"""
from collections.abc import Sequence
from typing import Any

from src.components.filter.basic import basic_filter
from src.components.filter.protocol import FilterFn

_DEFAULT: Sequence[FilterFn] = [basic_filter]


def filter(data: Any, fns: Sequence[FilterFn] = _DEFAULT) -> Any:  # noqa: A001
    """Apply each filter function sequentially; output of one is input of next."""
    for fn in fns:
        data = fn(data)
    return data
