"""Typed public tools and exact manifest execution against safe local abstractions."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from threading import RLock
from typing import Any

from .contracts import ActionKind, ActionRequest, ActionResult, RiskLevel, RunIdentity
from .control import CancellationToken
from .manifests import ActionManifest, ManifestRegistry
from .state import ArtifactStore


class ToolValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    action: ActionKind
    risk: RiskLevel
    required_arguments: frozenset[str]
    handler: Callable[[Mapping[str, Any], RunIdentity], ActionResult]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._lock = RLock()

    def register(self, spec: ToolSpec, *, replace: bool = False) -> None:
        with self._lock:
            if spec.name in self._tools and not replace:
                raise ValueError(f"tool already registered: {spec.name}")
            self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        with self._lock:
            spec = self._tools.get(name)
        if spec is None:
            raise KeyError(f"unknown tool: {name}")
        return spec

    def validate(self, request: ActionRequest) -> ToolSpec:
        spec = self.get(request.tool)
        missing = spec.required_arguments - set(request.arguments)
        if missing:
            raise ToolValidationError(f"{request.tool} missing arguments: {sorted(missing)}")
        if request.action is not spec.action or request.risk is not spec.risk:
            raise ToolValidationError("action authority differs from registered tool contract")
        return spec


class PublicToolExecutor:
    """Claims one manifest and executes only its server-captured actions."""

    def __init__(self, registry: ToolRegistry, manifests: ManifestRegistry) -> None:
        self.registry = registry
        self.manifests = manifests

    def execute_manifest(
        self,
        manifest: ActionManifest,
        identity: RunIdentity,
        token: CancellationToken,
    ) -> tuple[ActionResult, ...]:
        claimed = self.manifests.claim(manifest.manifest_id, identity, manifest.actions)
        results: list[ActionResult] = []
        success = False
        try:
            for payload in claimed.actions:
                token.raise_if_cancelled()
                request = ActionRequest(
                    tool=str(payload["tool"]),
                    arguments=dict(payload["arguments"]),
                    action=ActionKind(str(payload["action"])),
                    risk=RiskLevel(str(payload["risk"])),
                )
                spec = self.registry.validate(request)
                result = spec.handler(request.arguments, identity)
                results.append(result)
                if not result.success:
                    break
            success = bool(results) and all(result.success for result in results)
            return tuple(results)
        finally:
            self.manifests.complete(claimed.manifest_id, success=success)


def default_tool_registry(artifact_store: ArtifactStore) -> ToolRegistry:
    registry = ToolRegistry()

    def inspect_text(arguments: Mapping[str, Any], identity: RunIdentity) -> ActionResult:
        text = str(arguments["text"])
        words = [word for word in text.split() if word]
        return ActionResult(
            "inspect_text",
            True,
            f"inspected {len(words)} words for run {identity.run_id}",
        )

    def create_artifact(arguments: Mapping[str, Any], identity: RunIdentity) -> ActionResult:
        name = str(arguments["name"])
        content = str(arguments["content"]).encode()
        media_type = str(arguments.get("media_type", "text/plain"))
        ref = artifact_store.put(identity.tenant_id, name, content, media_type)
        return ActionResult(
            "create_artifact",
            True,
            f"created immutable artifact {name}",
            (ref.artifact_id,),
        )

    def simulated_network(arguments: Mapping[str, Any], identity: RunIdentity) -> ActionResult:
        resource = str(arguments["resource"])
        return ActionResult(
            "simulated_network",
            True,
            f"simulated read of {resource} for run {identity.run_id}",
        )

    def simulated_execution(arguments: Mapping[str, Any], identity: RunIdentity) -> ActionResult:
        instruction = str(arguments["instruction"])
        return ActionResult(
            "simulated_execution",
            True,
            f"simulated bounded execution for run {identity.run_id}: {instruction}",
        )

    registry.register(
        ToolSpec(
            "inspect_text",
            ActionKind.READ,
            RiskLevel.LOW,
            frozenset({"text"}),
            inspect_text,
        )
    )
    registry.register(
        ToolSpec(
            "create_artifact",
            ActionKind.WRITE,
            RiskLevel.HIGH,
            frozenset({"name", "content"}),
            create_artifact,
        )
    )
    registry.register(
        ToolSpec(
            "simulated_network",
            ActionKind.NETWORK,
            RiskLevel.MEDIUM,
            frozenset({"resource"}),
            simulated_network,
        )
    )
    registry.register(
        ToolSpec(
            "simulated_execution",
            ActionKind.EXECUTE,
            RiskLevel.HIGH,
            frozenset({"instruction"}),
            simulated_execution,
        )
    )
    return registry


def plan_public_actions(
    instruction: str,
    expected_artifacts: Iterable[str],
    requested_action: ActionKind,
) -> tuple[ActionRequest, ...]:
    """Deterministic planner used only by the offline public scenarios."""

    artifacts = tuple(expected_artifacts)
    if artifacts:
        if requested_action is not ActionKind.WRITE:
            raise ToolValidationError("artifact creation requires write authority")
        return tuple(
            ActionRequest(
                "create_artifact",
                {
                    "name": name,
                    "content": f"Public simulation result for: {instruction}",
                    "media_type": "text/plain",
                },
                ActionKind.WRITE,
                RiskLevel.HIGH,
            )
            for name in artifacts
        )
    if requested_action is ActionKind.WRITE:
        raise ToolValidationError("public write requests require an expected artifact")
    if requested_action is ActionKind.NETWORK:
        return (
            ActionRequest(
                "simulated_network",
                {"resource": "public-offline-fixture"},
                ActionKind.NETWORK,
                RiskLevel.MEDIUM,
            ),
        )
    if requested_action is ActionKind.EXECUTE:
        return (
            ActionRequest(
                "simulated_execution",
                {"instruction": instruction},
                ActionKind.EXECUTE,
                RiskLevel.HIGH,
            ),
        )
    return (
        ActionRequest(
            "inspect_text",
            {"text": instruction},
            ActionKind.READ,
            RiskLevel.LOW,
        ),
    )
