import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = json.loads((ROOT / "machine" / "excellence-state.json").read_text(encoding="utf-8"))
POSITION = json.loads((ROOT / "machine" / "canonical-position.json").read_text(encoding="utf-8"))
CAPABILITIES = json.loads((ROOT / "machine" / "capabilities.json").read_text(encoding="utf-8"))


class CanonicalPositionContractTests(unittest.TestCase):
    def test_evolving_state_is_gate_complete(self):
        self.assertEqual(STATE["principal_state"], "EVOLVING")
        self.assertEqual(STATE["gates"]["CANONICAL_POSITION_RESOLVED"]["status"], "PASS")
        self.assertEqual(STATE["gates"]["EVOLUTION_CURSOR_DEFINED"]["status"], "PASS")
        self.assertEqual(STATE["canonical_position_ref"], "machine/canonical-position.json")

    def test_specialist_identity_and_lineage_are_preserved(self):
        self.assertEqual(POSITION["repository"], STATE["repository"])
        self.assertEqual(POSITION["role"], "company_specific_specialist_system")
        policy = POSITION["integration_policy"]
        self.assertTrue(policy["preserve_repository_identity"])
        self.assertTrue(policy["preserve_lineage"])
        self.assertTrue(policy["presentation_independent"])
        self.assertTrue(policy["absorption_requires_functional_equivalence"])
        self.assertTrue(policy["absorption_requires_proof_equivalence"])

    def test_capability_manifest_names_proven_mechanisms(self):
        caps = set(CAPABILITIES["capabilities"])
        self.assertIn("policy-hash-binding", caps)
        self.assertIn("deterministic-allow-refuse-replay", caps)
        self.assertIn("hard-red-line-refusal", caps)
        self.assertNotIn("hyper-scaling", caps)

    def test_relationships_do_not_claim_integration(self):
        self.assertTrue(POSITION["relationships"])
        self.assertTrue(
            all(row["integration_state"] == "NOT_CLAIMED" for row in POSITION["relationships"])
        )

    def test_evolution_is_material(self):
        self.assertTrue(STATE["evolution_cursor"].startswith("next:"))
        self.assertIn("policy-version", POSITION["next_evolution"])
        self.assertIn("tampering", POSITION["next_evolution"])


if __name__ == "__main__":
    unittest.main()
