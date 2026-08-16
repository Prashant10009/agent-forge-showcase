import unittest

from agent_forge_public.contracts import RunIdentity
from agent_forge_public.protocols import (
    ProtocolBoundaryError,
    ProtocolKind,
    ProtocolRegistry,
    ProtocolRequest,
    ProtocolResponse,
)


class LocalAdapter:
    kind = ProtocolKind.MCP
    capabilities = frozenset({"inspect"})

    def __init__(self):
        self.identity = None

    def invoke(self, request):
        self.identity = request.identity
        return ProtocolResponse(self.kind, request.operation, True, "local simulation")


class ProtocolBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.identity = RunIdentity("run", "tenant", "session", "turn")
        self.request = ProtocolRequest(self.identity, "inspect-schema", "inspect")

    def test_identity_reaches_registered_adapter(self):
        adapter = LocalAdapter()
        registry = ProtocolRegistry()
        registry.register(adapter)
        response = registry.invoke(ProtocolKind.MCP, self.request)
        self.assertTrue(response.accepted)
        self.assertEqual(adapter.identity, self.identity)

    def test_unregistered_protocol_is_denied(self):
        with self.assertRaises(ProtocolBoundaryError):
            ProtocolRegistry().invoke(ProtocolKind.MCP, self.request)

    def test_undeclared_capability_is_denied(self):
        registry = ProtocolRegistry()
        registry.register(LocalAdapter())
        request = ProtocolRequest(self.identity, "mutate", "write")
        with self.assertRaises(ProtocolBoundaryError):
            registry.invoke(ProtocolKind.MCP, request)

    def test_duplicate_protocol_registration_is_rejected(self):
        registry = ProtocolRegistry()
        registry.register(LocalAdapter())
        with self.assertRaises(ValueError):
            registry.register(LocalAdapter())
