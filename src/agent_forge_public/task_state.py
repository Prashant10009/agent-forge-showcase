"""Tenant-scoped vector contracts for public task-state retrieval examples."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Mapping, Sequence

from .state import TenantBoundaryError


class VectorContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class VectorSpace:
    name: str
    dimensions: int

    def __post_init__(self) -> None:
        if not self.name.strip() or self.dimensions < 1:
            raise VectorContractError("vector space requires a name and positive dimensions")

    def validate(self, vector: Sequence[float]) -> tuple[float, ...]:
        values = tuple(float(value) for value in vector)
        if len(values) != self.dimensions:
            raise VectorContractError(
                f"expected {self.dimensions} dimensions, received {len(values)}"
            )
        if not all(math.isfinite(value) for value in values):
            raise VectorContractError("vector values must be finite")
        return values


@dataclass(frozen=True, slots=True)
class TaskVectorRecord:
    record_id: str
    tenant_id: str
    space: VectorSpace
    vector: tuple[float, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SimilarTask:
    record_id: str
    score: float
    metadata: Mapping[str, Any]


class TenantTaskIndex:
    """Small in-memory contract proving tenant and vector-space boundaries."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], TaskVectorRecord] = {}
        self._lock = RLock()

    def put(
        self,
        record_id: str,
        tenant_id: str,
        space: VectorSpace,
        vector: Sequence[float],
        metadata: Mapping[str, Any] | None = None,
    ) -> TaskVectorRecord:
        if not record_id.strip() or not tenant_id.strip():
            raise ValueError("record_id and tenant_id cannot be empty")
        record = TaskVectorRecord(
            record_id,
            tenant_id,
            space,
            space.validate(vector),
            dict(metadata or {}),
        )
        with self._lock:
            self._records[(tenant_id, record_id)] = record
        return record

    def get(self, record_id: str, tenant_id: str) -> TaskVectorRecord:
        with self._lock:
            record = self._records.get((tenant_id, record_id))
            if record is not None:
                return record
            if any(key[1] == record_id for key in self._records):
                raise TenantBoundaryError("task vector belongs to another tenant")
        raise KeyError("unknown task vector")

    def search(
        self,
        tenant_id: str,
        space: VectorSpace,
        query: Sequence[float],
        *,
        limit: int = 5,
    ) -> tuple[SimilarTask, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        query_vector = space.validate(query)
        with self._lock:
            candidates = tuple(
                record
                for (owner, _), record in self._records.items()
                if owner == tenant_id and record.space == space
            )
        ranked = sorted(
            (
                SimilarTask(
                    record.record_id,
                    round(_cosine(query_vector, record.vector), 6),
                    dict(record.metadata),
                )
                for record in candidates
            ),
            key=lambda result: (-result.score, result.record_id),
        )
        return tuple(ranked[:limit])


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )
