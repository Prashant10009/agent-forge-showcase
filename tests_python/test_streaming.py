import unittest

from agent_forge_public.streaming import (
    StreamContractError,
    StreamEventKind,
    StreamLifecycle,
)


class MutableClock:
    def __init__(self):
        self.value = 10.0

    def __call__(self):
        return self.value


class StreamingContractTests(unittest.TestCase):
    def test_partial_output_survives_inactivity_cutoff(self):
        clock = MutableClock()
        stream = StreamLifecycle(1000, clock=clock)
        stream.delta("Hello ")
        stream.delta("world")
        clock.value += 1.1
        terminal = stream.close_if_inactive()
        self.assertEqual(terminal.kind, StreamEventKind.DONE)
        self.assertEqual(terminal.text, "Hello world")
        self.assertEqual(terminal.finish_reason, "inactivity_cutoff")
        self.assertTrue(terminal.details["partial_preserved"])

    def test_empty_stall_is_incomplete_not_success(self):
        clock = MutableClock()
        stream = StreamLifecycle(1000, clock=clock)
        clock.value += 1.1
        self.assertEqual(stream.close_if_inactive().kind, StreamEventKind.INCOMPLETE)

    def test_steady_heartbeat_prevents_cutoff(self):
        clock = MutableClock()
        stream = StreamLifecycle(1000, clock=clock)
        clock.value += 0.8
        stream.heartbeat()
        clock.value += 0.8
        self.assertIsNone(stream.close_if_inactive())

    def test_exactly_one_terminal_event_is_allowed(self):
        stream = StreamLifecycle(1000)
        stream.finish(StreamEventKind.DONE, text="complete")
        with self.assertRaises(StreamContractError):
            stream.finish(StreamEventKind.ERROR, reason="late")

    def test_early_eof_is_visible(self):
        stream = StreamLifecycle(1000)
        stream.delta("partial")
        with self.assertRaisesRegex(StreamContractError, "without a terminal"):
            stream.require_terminal()

    def test_sequences_are_monotonic(self):
        stream = StreamLifecycle(1000, clock=lambda: 5.0)
        stream.delta("a")
        stream.heartbeat()
        stream.finish()
        self.assertEqual([event.sequence for event in stream.snapshot()], [1, 2, 3])
