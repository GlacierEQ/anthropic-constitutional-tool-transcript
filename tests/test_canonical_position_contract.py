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

    def test_identity_lineage_and_specialist_ownership_are_preserved(self):
        self.assertEqual(POSITION["repository"], STATE["repository"])
        self.assertEqual(POSITION["position_state"], "RESOLVED")
        self.assertEqual(POSITION["canonical_identity"], "constitutional-tool-transcript")
        self.assertEqual(POSITION["role"], "company_specific_specialist_system")
        policy = POSITION["integration_policy"]
        self.assertTrue(policy["preserve_repository_identity"])
        self.assertTrue(policy["preserve_lineage"])
        self.assertTrue(policy["presentation_independent"])
        self.assertTrue(policy["absorption_requires_functional_equivalence"])
        self.assertTrue(policy["absorption_requires_proof_equivalence"])

    def test_capability_manifest_names_repository_native_mechanisms(self):
        self.assertEqual(
            CAPABILITIES["capability_family"], "policy_bound_tool_decision_transcripts"
        )
        capabilities = set(CAPABILITIES["capabilities"])
        self.assertIn("policy-hash-bound-tool-decisions", capabilities)
        self.assertIn("deterministic-allow-refuse-replay", capabilities)
        self.assertIn("hard-red-line-refusal", capabilities)
        self.assertIn("deterministic-decision-fingerprints", capabilities)
        self.assertNotIn("hyper-scaling", capabilities)

    def test_evolution_is_material_and_claim_boundary_is_preserved(self):
        self.assertTrue(STATE["evolution_cursor"].startswith("next:"))
        self.assertTrue(POSITION["next_evolution"])
        self.assertIn("no Anthropic affiliation", POSITION["nonclaims"])
        self.assertIn("No Anthropic adoption", CAPABILITIES["truth_boundary"])


if __name__ == "__main__":
    unittest.main()
