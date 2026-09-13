"""Provider-neutral specialist worker templates for the public reference core.

This module is independently authored for the public showcase. It represents the
reusable configured-worker layer without pretending that the whole Agent Forge
control plane is made from one generic agent abstraction.

Production facts verified before publication:
- the private system has a reusable configured worker pool;
- those workers are created from configuration by a factory;
- control/intelligence systems such as the Orchestrator, Trimurti, Karma, RTA,
  and sentinel gates are separate Python subsystems;
- runtime/model selection remains separable from worker responsibility.

The public catalog below is synthetic. It contains no private worker prompts, exact
production inventory, provider/model identities, routing policy, thresholds, or
learned parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .contracts import WorkRequest
from .models import Capability


class WorkerKind(str, Enum):
    GENERAL = "general"
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    DOCUMENT = "document"
    VISION = "vision"


@dataclass(frozen=True, slots=True)
class SpecialistWorkerTemplate:
    kind: WorkerKind
    responsibility: str
    required: tuple[Capability, ...]
    preferred: tuple[Capability, ...] = ()


PUBLIC_WORKER_TEMPLATES: dict[WorkerKind, SpecialistWorkerTemplate] = {
    WorkerKind.GENERAL: SpecialistWorkerTemplate(
        WorkerKind.GENERAL,
        "general text work with optional reasoning support",
        (Capability.TEXT,),
        (Capability.REASONING,),
    ),
    WorkerKind.CODING: SpecialistWorkerTemplate(
        WorkerKind.CODING,
        "software implementation and code-oriented problem solving",
        (Capability.TEXT, Capability.CODE),
        (Capability.REASONING, Capability.TOOLS),
    ),
    WorkerKind.RESEARCH: SpecialistWorkerTemplate(
        WorkerKind.RESEARCH,
        "research, synthesis, and evidence-oriented investigation",
        (Capability.TEXT, Capability.REASONING),
        (Capability.DATA, Capability.TOOLS),
    ),
    WorkerKind.ANALYSIS: SpecialistWorkerTemplate(
        WorkerKind.ANALYSIS,
        "structured analysis of data and business or technical questions",
        (Capability.TEXT, Capability.DATA),
        (Capability.REASONING,),
    ),
    WorkerKind.DOCUMENT: SpecialistWorkerTemplate(
        WorkerKind.DOCUMENT,
        "document understanding, transformation, and structured extraction",
        (Capability.TEXT,),
        (Capability.DATA, Capability.REASONING),
    ),
    WorkerKind.VISION: SpecialistWorkerTemplate(
        WorkerKind.VISION,
        "visual understanding combined with text-based reasoning",
        (Capability.TEXT, Capability.VISION),
        (Capability.REASONING,),
    ),
}


def _merge_capabilities(
    first: tuple[Capability, ...],
    second: tuple[Capability, ...],
) -> tuple[Capability, ...]:
    return tuple(dict.fromkeys((*first, *second)))


def apply_worker_template(
    request: WorkRequest,
    worker: WorkerKind | str,
) -> WorkRequest:
    """Attach worker requirements without choosing an execution runtime."""

    resolved = WorkerKind(worker)
    spec = PUBLIC_WORKER_TEMPLATES[resolved]
    metadata = dict(request.metadata)
    metadata.update(
        {
            "specialist_worker": spec.kind.value,
            "worker_responsibility": spec.responsibility,
            "worker_layer": "public-synthetic-configured-worker",
        }
    )
    return replace(
        request,
        required=_merge_capabilities(spec.required, request.required),
        preferred=_merge_capabilities(spec.preferred, request.preferred),
        metadata=metadata,
    )


def describe_worker(worker: WorkerKind | str) -> dict[str, object]:
    spec = PUBLIC_WORKER_TEMPLATES[WorkerKind(worker)]
    return {
        "worker": spec.kind.value,
        "responsibility": spec.responsibility,
        "required": [capability.value for capability in spec.required],
        "preferred": [capability.value for capability in spec.preferred],
        "runtime_bound": False,
        "control_plane_component": False,
        "synthetic_public_template": True,
    }
