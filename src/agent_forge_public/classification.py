"""Transparent task classification used by the public reference core."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Capability


@dataclass(frozen=True, slots=True)
class Classification:
    kind: str
    required: tuple[Capability, ...]
    preferred: tuple[Capability, ...]
    evidence: tuple[str, ...]


_PROFILES: dict[str, tuple[tuple[str, ...], tuple[Capability, ...], tuple[Capability, ...]]] = {
    "code": (
        ("code", "implement", "function", "refactor", "debug", "python", "javascript"),
        (Capability.TEXT, Capability.CODE),
        (Capability.TOOLS,),
    ),
    "data": (
        ("csv", "dataset", "schema", "query", "table", "transform", "parse"),
        (Capability.TEXT, Capability.DATA),
        (Capability.CODE,),
    ),
    "tools": (
        ("execute", "command", "shell", "build", "compile", "deploy", "run tests"),
        (Capability.TEXT, Capability.TOOLS),
        (Capability.CODE,),
    ),
    "vision": (
        ("image", "screenshot", "diagram", "photo", "visual"),
        (Capability.TEXT, Capability.VISION),
        (),
    ),
    "reasoning": (
        ("analyze", "plan", "architect", "compare", "evaluate", "explain", "research"),
        (Capability.TEXT, Capability.REASONING),
        (),
    ),
}


def classify(instruction: str) -> Classification:
    """Classify an instruction and expose every keyword used as evidence."""

    normalized = instruction.casefold()
    ranked: list[tuple[int, int, str, tuple[str, ...], tuple[Capability, ...], tuple[Capability, ...]]] = []
    for order, (kind, (keywords, required, preferred)) in enumerate(_PROFILES.items()):
        evidence = tuple(keyword for keyword in keywords if keyword in normalized)
        ranked.append((len(evidence), -order, kind, evidence, required, preferred))

    score, _, kind, evidence, required, preferred = max(ranked)
    if score == 0:
        return Classification("general", (Capability.TEXT,), (Capability.REASONING,), ())
    return Classification(kind, required, preferred, evidence)
