"""Tests for the transform component."""

from typing import Any

from src.components.transform import transform as apply_transform
from src.components.transform.basic import basic_transform


def test_basic_transform_is_identity() -> None:
    assert basic_transform("hello") == "hello"
    assert basic_transform(42) == 42


def test_transform_applies_default_pipeline() -> None:
    result = apply_transform("data")
    assert result == "data"


def test_transform_applies_custom_fns_sequentially() -> None:
    def double(data: Any) -> Any:
        return str(data) * 2

    def upper(data: Any) -> Any:
        return str(data).upper()

    assert apply_transform("x", fns=[double, upper]) == "XX"


def test_transform_with_empty_fns_returns_data_unchanged() -> None:
    assert apply_transform("data", fns=[]) == "data"
