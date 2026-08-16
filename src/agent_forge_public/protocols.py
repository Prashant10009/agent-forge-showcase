"""Neutral protocol boundaries for external tool and agent interoperability."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Mapping, Protocol, runtime_checkable

from .contracts import RunIdentity


class ProtocolKind(str, Enum):
    MCP = "mcp"
    A2A = "a2a"


class ProtocolBoundaryError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProtocolRequest:
    identity: RunIdentity
    operation: str
    capability: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.operation.strip() or not self.capability.strip():
            raise ValueError("operation and capability cannot be empty")


@dataclass(frozen=True, slots=True)
class ProtocolResponse:
    protocol: ProtocolKind
    operation: str
    accepted: bool
    summary: str


@runtime_checkable
class ProtocolAdapter(Protocol):
    kind: ProtocolKind
    capabilities: frozenset[str]

    def invoke(self, request: ProtocolRequest) -> ProtocolResponse: ...


class ProtocolRegistry:
    """Selects an explicitly registered protocol without network configuration."""

    def __init__(self) -> None:
        self._adapters: dict[ProtocolKind, ProtocolAdapter] = {}
        self._lock = RLock()

    def register(self, adapter: ProtocolAdapter) -> None:
        with self._lock:
            if adapter.kind in self._adapters:
                raise ValueError(f"protocol already registered: {adapter.kind.value}")
            self._adapters[adapter.kind] = adapter

    def invoke(self, kind: ProtocolKind, request: ProtocolRequest) -> ProtocolResponse:
        with self._lock:
            adapter = self._adapters.get(kind)
        if adapter is None:
            raise ProtocolBoundaryError(f"protocol is not registered: {kind.value}")
        if request.capability not in adapter.capabilities:
            raise ProtocolBoundaryError(
                f"capability is not authorized for {kind.value}: {request.capability}"
            )
        response = adapter.invoke(request)
        if response.protocol is not kind or response.operation != request.operation:
            raise ProtocolBoundaryError("adapter response does not match request envelope")
        return response
