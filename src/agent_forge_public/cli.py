"""Command-line entrypoint for the runnable public core."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .models import ActionKind
from .orchestrator import AgentForge
from .scenarios import SCENARIOS, run_all_scenarios, run_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-forge-public",
        description="Run the provider-neutral Agent Forge public core.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run a governed offline code task")
    demo.add_argument(
        "instruction",
        nargs="?",
        default="Implement a Python parser and write the result",
    )
    demo.add_argument(
        "--action",
        choices=[action.value for action in ActionKind],
        default=ActionKind.WRITE.value,
        help="authority class used by the approval policy (default: write)",
    )
    demo.add_argument("--approve", action="store_true", help="approve and resume the write action")

    route = subparsers.add_parser("route", help="inspect routing without execution")
    route.add_argument("instruction")

    lab = subparsers.add_parser("lab", help="run resilience and governance scenarios")
    lab.add_argument("scenario", choices=(*SCENARIOS, "all"), default="all", nargs="?")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    forge = AgentForge()

    if args.command == "lab":
        payload = run_all_scenarios() if args.scenario == "all" else run_scenario(args.scenario)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "route":
        task = forge.make_task(args.instruction, action=ActionKind.READ)
        decision = forge.router.choose(task, forge.registry.descriptors())
        print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
        return 0

    task = forge.make_task(args.instruction, action=ActionKind(args.action))
    outcome = forge.submit(task)
    if args.approve and outcome.approval:
        outcome = forge.resume(outcome.approval.approval_id, outcome.approval.challenge)
    print(json.dumps(outcome.to_dict(), indent=2, sort_keys=True))
    return 0
