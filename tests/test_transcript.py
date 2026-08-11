from __future__ import annotations
import math
import unittest
from src.transcript import (
    ConstitutionalTranscript,
    Policy,
    ToolCall,
    ToolSchemaRef,
    Verdict,
    verify_replay_receipt,
)

SCHEMA_SEARCH = "a" * 64
SCHEMA_READ = "b" * 64


class TxTests(unittest.TestCase):
    def setUp(self):
        self.pol = Policy(
            "p1",
            frozenset({"bash"}),
            frozenset({"read_file", "search"}),
            {
                "search": ToolSchemaRef("search", "v1", SCHEMA_SEARCH),
                "read_file": ToolSchemaRef("read_file", "v2", SCHEMA_READ),
            },
        )
        self.tx = ConstitutionalTranscript(self.pol)

    def test_red_line_dominates_schema_state(self):
        entry = self.tx.decide(ToolCall("c1", "bash", {"cmd": "rm"}))
        self.assertEqual(entry.verdict, Verdict.REFUSE)
        self.assertEqual(entry.reason, "RED_LINE")

    def test_allowed_call_requires_exact_schema_version(self):
        entry = self.tx.decide(ToolCall("c1", "search", {"q": "a"}, "v1"))
        self.assertEqual(entry.verdict, Verdict.ALLOW)
        self.assertEqual(entry.reason, "POLICY_ALLOW")
        self.assertEqual(entry.schema_digest, SCHEMA_SEARCH)

        bad = ConstitutionalTranscript(self.pol).decide(
            ToolCall("c2", "search", {"q": "a"}, "v2")
        )
        self.assertEqual(bad.verdict, Verdict.REFUSE)
        self.assertEqual(bad.reason, "SCHEMA_VERSION_MISMATCH")

    def test_unbound_allowed_tool_refuses(self):
        policy = Policy("p2", frozenset(), frozenset({"search"}))
        entry = ConstitutionalTranscript(policy).decide(
            ToolCall("c1", "search", {"q": "a"}, "v1")
        )
        self.assertEqual(entry.verdict, Verdict.REFUSE)
        self.assertEqual(entry.reason, "SCHEMA_UNBOUND")

    def test_call_id_is_one_shot_and_exact_replay_is_idempotent(self):
        call = ToolCall("c1", "search", {"q": "a"}, "v1")
        first = self.tx.decide(call)
        second = self.tx.decide(call)
        self.assertEqual(first, second)
        self.assertEqual(len(self.tx.entries), 1)
        with self.assertRaisesRegex(ValueError, "CALL_ID_REBOUND"):
            self.tx.decide(ToolCall("c1", "search", {"q": "changed"}, "v1"))
        self.assertEqual(len(self.tx.entries), 1)

    def test_argument_content_changes_fingerprint(self):
        a = ConstitutionalTranscript(self.pol).decide(
            ToolCall("c1", "search", {"q": "alpha"}, "v1")
        )
        b = ConstitutionalTranscript(self.pol).decide(
            ToolCall("c1", "search", {"q": "beta"}, "v1")
        )
        self.assertNotEqual(a.input_digest, b.input_digest)
        self.assertNotEqual(a.fingerprint, b.fingerprint)

    def test_object_key_order_does_not_change_identity(self):
        a = ConstitutionalTranscript(self.pol).decide(
            ToolCall("c1", "search", {"q": "alpha", "limit": 3}, "v1")
        )
        b = ConstitutionalTranscript(self.pol).decide(
            ToolCall("c1", "search", {"limit": 3, "q": "alpha"}, "v1")
        )
        self.assertEqual(a.input_digest, b.input_digest)
        self.assertEqual(a.fingerprint, b.fingerprint)

    def test_hash_chain_binds_order(self):
        first = self.tx.decide(ToolCall("c1", "search", {"q": "a"}, "v1"))
        second = self.tx.decide(ToolCall("c2", "read_file", {"path": "x"}, "v2"))
        self.assertEqual(second.sequence, 1)
        self.assertEqual(second.prev_fingerprint, first.fingerprint)

        reverse = ConstitutionalTranscript(self.pol)
        reverse.decide(ToolCall("c2", "read_file", {"path": "x"}, "v2"))
        reverse_second = reverse.decide(ToolCall("c1", "search", {"q": "a"}, "v1"))
        self.assertNotEqual(second.fingerprint, reverse_second.fingerprint)

    def test_replay_receipt_is_recomputable_and_tamper_evident(self):
        calls = [
            ToolCall("c1", "search", {"q": "a"}, "v1"),
            ToolCall("c2", "bash", {"cmd": "rm"}),
        ]
        receipt = self.tx.make_replay_receipt(calls)
        self.assertTrue(verify_replay_receipt(self.pol, calls, receipt))
        self.assertFalse(
            verify_replay_receipt(
                self.pol,
                [ToolCall("c1", "search", {"q": "tampered"}, "v1"), calls[1]],
                receipt,
            )
        )
        self.assertFalse(verify_replay_receipt(self.pol, list(reversed(calls)), receipt))

    def test_duplicate_exact_call_is_visible_in_replay_counts(self):
        call = ToolCall("c1", "search", {"q": "a"}, "v1")
        receipt = self.tx.make_replay_receipt([call, call])
        self.assertEqual(receipt.requested_call_count, 2)
        self.assertEqual(receipt.unique_entry_count, 1)
        self.assertTrue(verify_replay_receipt(self.pol, [call, call], receipt))

    def test_schema_change_changes_policy_identity(self):
        changed = Policy(
            "p1",
            self.pol.red_lines,
            self.pol.allowed_tools,
            {
                "search": ToolSchemaRef("search", "v9", SCHEMA_SEARCH),
                "read_file": ToolSchemaRef("read_file", "v2", SCHEMA_READ),
            },
        )
        self.assertNotEqual(self.pol.policy_hash(), changed.policy_hash())

    def test_python_node_cross_runtime_vector(self):
        self.assertEqual(
            self.pol.policy_hash(),
            "075dd3ae76e93ef50bdf66c30fc13460a670862d2feac498c70acc0e7db3054b",
        )
        call = ToolCall("c1", "search", {"limit": 3, "q": "alpha"}, "v1")
        entry = ConstitutionalTranscript(self.pol).decide(call)
        self.assertEqual(
            entry.input_digest,
            "ff5d94363ebe944a5c358837999adc932ba2607d24d9f4bb1dee5cb797b7058a",
        )
        self.assertEqual(
            entry.fingerprint,
            "36670378e869a7b117b2e936c8667729a6a922aab00769aeba29789c7bfc2e99",
        )
        receipt = ConstitutionalTranscript(self.pol).make_replay_receipt([call])
        self.assertEqual(
            receipt.fingerprint,
            "4046d428ce97bbac5fb6d7baaf9b1a7cdd55ffd1fa4be0753696f7a79030d61d",
        )

    def test_malformed_json_evidence_fails_closed(self):
        with self.assertRaises(ValueError):
            ToolCall("c1", "search", {"score": math.nan}, "v1")
        with self.assertRaises(TypeError):
            ToolCall("c1", "search", {"bad": {"set"}}, "v1")
        with self.assertRaises(ValueError):
            ToolSchemaRef("search", "v1", "not-a-digest")

    def test_replay_identical(self):
        calls = [
            ToolCall("c1", "search", {"q": "a"}, "v1"),
            ToolCall("c2", "bash", {}),
        ]
        a = [self.tx.decide(c) for c in calls]
        b = self.tx.replay(calls)
        self.assertEqual([x.fingerprint for x in a], [x.fingerprint for x in b])


if __name__ == "__main__":
    unittest.main()
