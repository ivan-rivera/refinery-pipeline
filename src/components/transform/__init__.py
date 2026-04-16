"""Transform component.

Usage:
    from src.components.transform import transform as apply_transform
    result = apply_transform(data)                       # uses _DEFAULT
    result = apply_transform(data, fns=[my_transform])   # custom sequence
"""
from collections.abc import Sequence
from typing import Any

from src.components.transform.basic import basic_transform
from src.components.transform.protocol import TransformFn

_DEFAULT: Sequence[TransformFn] = [basic_transform]


def transform(data: Any, fns: Sequence[TransformFn] = _DEFAULT) -> Any:
    """Apply each transform function sequentially; output of one is input of next."""
    for fn in fns:
        data = fn(data)
    return data
