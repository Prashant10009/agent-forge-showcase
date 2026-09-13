"""Verified high-level Agent Forge topology for the public showcase.

This is an independently authored public representation, not a production package
map. It exists to prevent one misleading simplification: Agent Forge is not a set of
identical generic agents. The control plane contains distinct Python subsystems, while
reusable configured workers and replaceable execution runtimes occupy separate layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComponentLayer(str, Enum):
    CONTROL = "control"
    DELIBERATION = "deliberation"
    VALIDATION = "validation"
    INTELLIGENCE = "intelligence"
    RUNTIME_STATE = "runtime_state"
    CONFIGURED_WORKERS = "configured_workers"
    EXECUTION = "execution"


@dataclass(frozen=True, slots=True)
class PublicComponent:
    name: str
    layer: ComponentLayer
    responsibility: str
    generic_worker: bool


VERIFIED_PUBLIC_TOPOLOGY: tuple[PublicComponent, ...] = (
    PublicComponent(
        "Orchestrator",
        ComponentLayer.CONTROL,
        "owns the request lifecycle and wires routing, memory, deliberation, tools, and worker creation",
        False,
    ),
    PublicComponent(
        "Trimurti",
        ComponentLayer.DELIBERATION,
        "per-request and background deliberation subsystem with its own memory and pipeline components",
        False,
    ),
    PublicComponent(
        "Sentinel gates",
        ComponentLayer.VALIDATION,
        "validate selected tool/output paths at control boundaries",
        False,
    ),
    PublicComponent(
        "Karma",
        ComponentLayer.INTELLIGENCE,
        "monitoring and outcome/capability evidence that can inform routing decisions",
        False,
    ),
    PublicComponent(
        "RTA",
        ComponentLayer.RUNTIME_STATE,
        "runtime-state and decision subsystem covering backend lifecycle, flow, capacity, and strategy signals",
        False,
    ),
    PublicComponent(
        "Configured specialist workers",
        ComponentLayer.CONFIGURED_WORKERS,
        "reusable worker definitions instantiated from configuration and dispatched for specialist work",
        True,
    ),
    PublicComponent(
        "Execution runtimes",
        ComponentLayer.EXECUTION,
        "replaceable model/backend resources used to perform computation",
        False,
    ),
)


def topology_snapshot() -> list[dict[str, object]]:
    return [
        {
            "name": component.name,
            "layer": component.layer.value,
            "responsibility": component.responsibility,
            "generic_worker": component.generic_worker,
        }
        for component in VERIFIED_PUBLIC_TOPOLOGY
    ]
