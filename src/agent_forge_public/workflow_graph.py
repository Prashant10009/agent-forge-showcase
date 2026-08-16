"""Topology-preserving parallel workflow execution with explicit node outcomes."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

from .control import CancellationToken, RunCancelled


class NodeState(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class InvalidWorkflow(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class WorkNode:
    node_id: str
    instruction: str
    depends_on: tuple[str, ...] = ()
    continue_on_dependency_failure: bool = False

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.instruction.strip():
            raise ValueError("node_id and instruction cannot be empty")
        if self.node_id in self.depends_on:
            raise InvalidWorkflow("a node cannot depend on itself")


@dataclass(frozen=True, slots=True)
class NodeOutcome:
    node_id: str
    state: NodeState
    output: str = ""
    error: str = ""
    dependency_context: tuple[str, ...] = ()


class WorkflowGraph:
    def __init__(self, nodes: Iterable[WorkNode]) -> None:
        node_list = tuple(nodes)
        self.nodes = {node.node_id: node for node in node_list}
        if len(self.nodes) != len(node_list):
            raise InvalidWorkflow("node IDs must be unique")
        known = set(self.nodes)
        for node in self.nodes.values():
            missing = set(node.depends_on) - known
            if missing:
                raise InvalidWorkflow(
                    f"{node.node_id} has unknown dependencies: {sorted(missing)}"
                )
        self._waves = self._build_waves()

    @property
    def waves(self) -> tuple[tuple[WorkNode, ...], ...]:
        return self._waves

    def _build_waves(self) -> tuple[tuple[WorkNode, ...], ...]:
        remaining = set(self.nodes)
        completed: set[str] = set()
        waves: list[tuple[WorkNode, ...]] = []
        while remaining:
            ready = sorted(
                node_id
                for node_id in remaining
                if set(self.nodes[node_id].depends_on) <= completed
            )
            if not ready:
                raise InvalidWorkflow("workflow contains a dependency cycle")
            waves.append(tuple(self.nodes[node_id] for node_id in ready))
            completed.update(ready)
            remaining.difference_update(ready)
        return tuple(waves)


class WorkflowScheduler:
    """Runs independent nodes concurrently and preserves dependency failure context."""

    def __init__(
        self,
        executor: Callable[[WorkNode, CancellationToken, tuple[NodeOutcome, ...]], str],
        max_workers: int = 4,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self.executor = executor
        self.max_workers = max_workers

    def run(
        self,
        graph: WorkflowGraph,
        token: CancellationToken,
    ) -> dict[str, NodeOutcome]:
        outcomes: dict[str, NodeOutcome] = {}
        for wave in graph.waves:
            token.raise_if_cancelled()
            runnable: list[tuple[WorkNode, tuple[NodeOutcome, ...]]] = []
            for node in wave:
                dependencies = tuple(outcomes[name] for name in node.depends_on)
                failed = tuple(
                    item.node_id
                    for item in dependencies
                    if item.state is not NodeState.COMPLETED
                )
                if failed and not node.continue_on_dependency_failure:
                    outcomes[node.node_id] = NodeOutcome(
                        node.node_id,
                        NodeState.SKIPPED,
                        error="dependency did not complete",
                        dependency_context=failed,
                    )
                else:
                    runnable.append((node, dependencies))

            if not runnable:
                continue
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(runnable))) as pool:
                futures = {
                    pool.submit(self.executor, node, token, dependencies): (node, dependencies)
                    for node, dependencies in runnable
                }
                for future in as_completed(futures):
                    node, dependencies = futures[future]
                    try:
                        output = future.result()
                        outcomes[node.node_id] = NodeOutcome(
                            node.node_id,
                            NodeState.COMPLETED,
                            output=output,
                            dependency_context=tuple(item.node_id for item in dependencies),
                        )
                    except RunCancelled as error:
                        outcomes[node.node_id] = NodeOutcome(
                            node.node_id,
                            NodeState.CANCELLED,
                            error=str(error),
                        )
                    except Exception as error:
                        outcomes[node.node_id] = NodeOutcome(
                            node.node_id,
                            NodeState.FAILED,
                            error=f"{type(error).__name__}: {error}",
                        )
        return outcomes
