from __future__ import annotations

from typing import Collection, Any, TypeVar

T = TypeVar("T")


def partition(data: Collection[T], max_size: int) -> Collection[Collection[T]]:
    return [data[i:i + max_size] for i in range(0, len(data), max_size)]
