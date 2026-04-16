"""Tests for the filter component."""

from typing import Any

from src.components.filter import filter as apply_filter
from src.components.filter.basic import basic_filter


def test_basic_filter_is_identity() -> None:
    assert basic_filter("hello") == "hello"
    assert basic_filter(42) == 42
    assert basic_filter([1, 2]) == [1, 2]


def test_filter_applies_default_pipeline() -> None:
    result = apply_filter("data")
    assert result == "data"


def test_filter_applies_custom_fns_sequentially() -> None:
    def add_a(data: Any) -> Any:
        return str(data) + "a"

    def add_b(data: Any) -> Any:
        return str(data) + "b"

    assert apply_filter("x", fns=[add_a, add_b]) == "xab"


def test_filter_with_empty_fns_returns_data_unchanged() -> None:
    assert apply_filter("data", fns=[]) == "data"
