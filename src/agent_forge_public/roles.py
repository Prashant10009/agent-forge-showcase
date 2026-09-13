"""Provider-neutral agent roles for the public Agent Forge reference core.

This module is independently authored for the public showcase. It demonstrates the
architectural distinction between an agent's responsibility and the runtime selected
to execute a particular task. It contains no production prompts, provider inventory,
routing weights, thresholds, learned parameters, or private role definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .contracts import WorkRequest
from .models import Capability


class AgentRole(str, Enum):
    GENERAL = "general"
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    DOCUMENT = "document"
    VISION = "vision"


@dataclass(frozen=True, slots=True)
class RoleSpec:
    role: AgentRole
    responsibility: str
    required: tuple[Capability, ...]
    preferred: tuple[Capability, ...] = ()


PUBLIC_ROLE_CATALOG: dict[AgentRole, RoleSpec] = {
    AgentRole.GENERAL: RoleSpec(
        AgentRole.GENERAL,
        "general text work with optional reasoning support",
        (Capability.TEXT,),
        (Capability.REASONING,),
    ),
    AgentRole.CODING: RoleSpec(
        AgentRole.CODING,
        "software implementation and code-oriented problem solving",
        (Capability.TEXT, Capability.CODE),
        (Capability.REASONING, Capability.TOOLS),
    ),
    AgentRole.RESEARCH: RoleSpec(
        AgentRole.RESEARCH,
        "research, synthesis, and evidence-oriented investigation",
        (Capability.TEXT, Capability.REASONING),
        (Capability.DATA, Capability.TOOLS),
    ),
    AgentRole.ANALYSIS: RoleSpec(
        AgentRole.ANALYSIS,
        "structured analysis of data and business or technical questions",
        (Capability.TEXT, Capability.DATA),
        (Capability.REASONING,),
    ),
    AgentRole.DOCUMENT: RoleSpec(
        AgentRole.DOCUMENT,
        "document understanding, transformation, and structured extraction",
        (Capability.TEXT,),
        (Capability.DATA, Capability.REASONING),
    ),
    AgentRole.VISION: RoleSpec(
        AgentRole.VISION,
        "visual understanding combined with text-based reasoning",
        (Capability.TEXT, Capability.VISION),
        (Capability.REASONING,),
    ),
}


def _merge_capabilities(
    first: tuple[Capability, ...],
    second: tuple[Capability, ...],
) -> tuple[Capability, ...]:
    """Preserve stable ordering while removing duplicate capabilities."""

    return tuple(dict.fromkeys((*first, *second)))


def apply_role(request: WorkRequest, role: AgentRole | str) -> WorkRequest:
    """Return a new request carrying public role requirements.

    The role contributes capability requirements and descriptive metadata only. It
    never names or selects a runtime. Runtime selection remains the router's job.
    """

    resolved_role = AgentRole(role)
    spec = PUBLIC_ROLE_CATALOG[resolved_role]
    metadata = dict(request.metadata)
    metadata.update(
        {
            "agent_role": spec.role.value,
            "role_responsibility": spec.responsibility,
            "role_layer": "public-demonstration",
        }
    )
    return replace(
        request,
        required=_merge_capabilities(spec.required, request.required),
        preferred=_merge_capabilities(spec.preferred, request.preferred),
        metadata=metadata,
    )


def describe_role(role: AgentRole | str) -> dict[str, object]:
    """Return an inspectable, provider-neutral description of a public role."""

    spec = PUBLIC_ROLE_CATALOG[AgentRole(role)]
    return {
        "role": spec.role.value,
        "responsibility": spec.responsibility,
        "required": [capability.value for capability in spec.required],
        "preferred": [capability.value for capability in spec.preferred],
        "runtime_bound": False,
    }
