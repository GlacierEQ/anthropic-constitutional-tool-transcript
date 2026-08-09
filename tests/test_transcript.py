from __future__ import annotations
import unittest
from src.transcript import ConstitutionalTranscript, Policy, ToolCall, Verdict

class TxTests(unittest.TestCase):
    def setUp(self):
        self.pol = Policy("p1", frozenset({"bash"}), frozenset({"read_file", "search"}))
        self.tx = ConstitutionalTranscript(self.pol)

    def test_red_line(self):
        e = self.tx.decide(ToolCall("c1", "bash", {"cmd": "rm"}))
        self.assertEqual(e.verdict, Verdict.REFUSE)
        self.assertEqual(e.reason, "RED_LINE")

    def test_replay_identical(self):
        calls = [ToolCall("c1", "search", {"q": "a"}), ToolCall("c2", "bash", {})]
        a = [self.tx.decide(c) for c in calls]
        b = self.tx.replay(calls)
        self.assertEqual([x.fingerprint for x in a], [x.fingerprint for x in b])

if __name__ == "__main__":
    unittest.main()
