"""Minimal governed Agent Forge public-core run."""

from agent_forge_public import ActionKind, AgentForge


forge = AgentForge()
task = forge.make_task(
    "Implement a Python parser and write the result",
    task_id="example-code-task",
    action=ActionKind.WRITE,
)

pending = forge.submit(task)
assert pending.approval is not None
print("approval preview:", pending.approval.public_dict())

completed = forge.resume(pending.approval.approval_id, pending.approval.challenge)
print("runtime:", completed.route.runtime_name)
print("result:", completed.result.output if completed.result else "")
print("trace events:", len(completed.trace))
