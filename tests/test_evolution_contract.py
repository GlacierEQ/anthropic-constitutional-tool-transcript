import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = json.loads((ROOT / "machine" / "excellence-state.json").read_text(encoding="utf-8"))
POSITION = json.loads((ROOT / "machine" / "canonical-position.json").read_text(encoding="utf-8"))
TARGET = json.loads((ROOT / "machine" / "target-contract.json").read_text(encoding="utf-8"))
RECEIPT_PATH = ROOT / "machine" / "evolution-receipts" / "2026-08-11-schema-bound-replay-receipts.json"
RECEIPT = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


class EvolutionContractTests(unittest.TestCase):
    def test_consumed_cursor_is_exact_proof_bound(self):
        self.assertEqual(RECEIPT["result"], "PASS")
        self.assertEqual(RECEIPT["candidate_source_sha"], "dd227bbf5a713463bb5f32317993d731b13a3257")
        self.assertEqual(RECEIPT["workflow_run"], 31462143129)
        event = STATE["evolution_history"][-1]
        self.assertEqual(event["consumed_cursor"], RECEIPT["consumed_cursor"])
        self.assertEqual(event["receipt"], str(RECEIPT_PATH.relative_to(ROOT)))

    def test_next_cursor_is_consistent(self):
        expected = "next:signed_schema_registry_authority_and_tool_result_receipt_binding"
        self.assertEqual(STATE["evolution_cursor"], expected)
        self.assertEqual(TARGET["next_evolution"], expected)
        self.assertEqual(RECEIPT["next_cursor"], expected)
        self.assertIn("authenticated registry authority", POSITION["next_evolution"])
        self.assertIn("tool-result receipts", POSITION["next_evolution"])

    def test_claim_ceiling_and_nonclaims_do_not_inflate(self):
        self.assertEqual(STATE["claim_ceiling"], "PROMOTED")
        boundary = " ".join(TARGET["nonclaims"]).lower()
        self.assertIn("no anthropic affiliation", boundary)
        self.assertIn("deterministic hashes rather than cryptographic signatures", boundary)
        self.assertIn("does not execute tools", boundary)


if __name__ == "__main__":
    unittest.main()
