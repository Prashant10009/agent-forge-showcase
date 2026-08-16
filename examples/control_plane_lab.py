"""Run one governed public-control-plane request without external services."""

from __future__ import annotations

import json

from agent_forge_public.control_plane import PublicControlPlane
from agent_forge_public.models import ActionKind


def main() -> None:
    plane = PublicControlPlane()
    request = plane.request(
        "Implement and verify a public architecture report",
        run_id="example-governed-run",
        action=ActionKind.WRITE,
        expected_artifacts=("architecture-report.txt",),
    )
    pending = plane.start(request)
    print("Paused state:", pending.state.value)
    print("Manifest fingerprint:", pending.manifest.fingerprint)

    completed = plane.approve(pending.manifest.manifest_id, request.identity)
    print(json.dumps(completed.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
