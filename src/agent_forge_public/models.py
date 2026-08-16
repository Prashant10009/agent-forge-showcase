"""Shared public capability and authority enums."""

from __future__ import annotations

from enum import Enum


class Capability(str, Enum):
    TEXT = "text"
    CODE = "code"
    REASONING = "reasoning"
    TOOLS = "tools"
    VISION = "vision"
    DATA = "data"


class ActionKind(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
