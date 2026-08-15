"""Dependency-aware wave planning and parallel task execution."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import ExecutionResult, TaskSpec


class InvalidTaskGraph(ValueError):
    pass


class DispatchFailure(RuntimeError):
    def __init__(self, failures: Mapping[str, Exception], partial: Mapping[str, ExecutionResult]) -> None:
        self.failures = dict(failures)
        self.partial = dict(partial)
        names = ", ".join(sorted(self.failures))
        super().__init__(f"task dispatch failed: {names}")


class TaskGraph:
    def __init__(self, tasks: Iterable[TaskSpec]) -> None:
        task_list = tuple(tasks)
        self.tasks = {task.task_id: task for task in task_list}
        if len(self.tasks) != len(task_list):
            raise InvalidTaskGraph("task IDs must be unique")
        self._validate_dependencies()
        self._waves = self._build_waves()

    def waves(self) -> tuple[tuple[TaskSpec, ...], ...]:
        return self._waves

    def _validate_dependencies(self) -> None:
        known = set(self.tasks)
        for task in self.tasks.values():
            missing = set(task.depends_on) - known
            if missing:
                raise InvalidTaskGraph(f"{task.task_id} has unknown dependencies: {sorted(missing)}")

    def _build_waves(self) -> tuple[tuple[TaskSpec, ...], ...]:
        remaining = set(self.tasks)
        completed: set[str] = set()
        waves: list[tuple[TaskSpec, ...]] = []
        while remaining:
            ready_ids = sorted(
                task_id
                for task_id in remaining
                if set(self.tasks[task_id].depends_on) <= completed
            )
            if not ready_ids:
                raise InvalidTaskGraph("task dependencies contain a cycle")
            wave = tuple(self.tasks[task_id] for task_id in ready_ids)
            waves.append(wave)
            completed.update(ready_ids)
            remaining.difference_update(ready_ids)
        return tuple(waves)


class GraphDispatcher:
    """Executes each dependency wave concurrently and stops on failure."""

    def __init__(self, executor: Callable[[TaskSpec], ExecutionResult], max_workers: int = 4) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self.executor = executor
        self.max_workers = max_workers

    def run(self, graph: TaskGraph) -> dict[str, ExecutionResult]:
        results: dict[str, ExecutionResult] = {}
        for wave in graph.waves():
            failures: dict[str, Exception] = {}
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(wave))) as pool:
                futures = {pool.submit(self.executor, task): task.task_id for task in wave}
                for future in as_completed(futures):
                    task_id = futures[future]
                    try:
                        results[task_id] = future.result()
                    except Exception as error:  # preserve the original failure for inspection
                        failures[task_id] = error
            if failures:
                raise DispatchFailure(failures, results)
        return results
