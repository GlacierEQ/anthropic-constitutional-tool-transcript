# Constitutional Tool Transcript

**Lens:** tool-use safety (Anthropic-class)  
**Innovation:** Every tool call bound to policy hash + red-lines; replay must reproduce allow/refuse bit-identically.

Pairs with `anthropic-safety-monitor` / `anthropic-agent-coordinator`.


## Claim ceiling (independent reference)

Independent GlacierEQ reference only. No company affiliation, employment, deployment,
endorsement, or proprietary access is claimed. Names label public problem spaces.


## Epistemology / Verification

**L0 (Presence):** Source modules (`src/transcript.py`, `src/promotion_authority.py`) and tests exist and import cleanly. Verified.

**L1 (Structure):** Public classes/functions (`ConstitutionalTranscript`, `Policy`, `ToolCall`, `ToolSchemaRef`, `Verdict`, `PromotionAuthority`, `verify_bound_grant`, `verify_replay_receipt`) exist with documented signatures. Verified.

**L2 (Behavior):** Python suite 26/26 passing; Node suite passing; `ruff check src/ tests/` clean; `scripts/operate.py` smoke passes. Verified.

### Aspirational (L0/L1 only, not L2)

- Authenticated schema-registry authority for tool schema references (not yet implemented).
- Verified tool-result receipts bound back into the transcript.
- Tool execution and tool-result verification (out of scope; transcript records decisions only).
- Cryptographic signatures (current receipts are deterministic hashes).
- Production deployment or exercised sibling integration.

### Verification commands

```bash
PYTHONPATH=src pytest tests/ -v
PYTHONPATH=src python scripts/operate.py
node ts/run_tests.mjs
/tmp/cu-venv/bin/ruff check src/ tests/
```

### Not claimed

No Anthropic affiliation, adoption, employment, or production safety-service deployment is claimed. This is an independent reference implementation; replay receipts are deterministic hashes, not signatures.

### Machine–Mesh Protocol Manifest

<!-- glacier-eq-protocol:start -->
```yaml
{
  "schema": "glacier-eq.readme.machine-mesh/v1",
  "repository": {
    "id": "GlacierEQ/anthropic-constitutional-tool-transcript",
    "url": "https://github.com/GlacierEQ/anthropic-constitutional-tool-transcript",
    "readme_contract": "estate-machine-v1",
    "default_branch": "main"
  },
  "machine": {
    "repository_kind": "migration-residue",
    "public_api": "inspect-declared-entrypoints",
    "protocol_files": [],
    "entrypoints": [
      {
        "kind": "source-area",
        "path": "src",
        "policy": "inspect-before-use"
      },
      {
        "kind": "script-area",
        "path": "scripts",
        "policy": "inspect-before-use"
      },
      {
        "kind": "test-area",
        "path": "tests",
        "policy": "run-before-reliance"
      },
      {
        "kind": "machine-contract-area",
        "path": "machine",
        "policy": "read-first"
      }
    ]
  },
  "presentation": {
    "architecture": [
      "recruiter",
      "master",
      "machine",
      "mesh"
    ],
    "authority": {
      "capability": "stone-psysoc-x",
      "repository": "GlacierEQ/AKOS",
      "manifest": "stones/psysoc-x/stone.json",
      "engine": "infinity_stones/psysoc_x.py"
    },
    "truth_invariant": "presentation-may-change-sequence-density-tone-and-style; facts-evidence-uncertainty-provenance-dignity-and-reader-agency-may-not"
  },
  "license": {
    "class": "EXISTING_LICENSE",
    "status": "CONTROLLING_LICENSE_CONTENT_REVIEW_REQUIRED",
    "controlling_path": "LICENSE",
    "policy": "GlacierEQ/job-app-helix/LICENSE_POLICY.json",
    "may_relicense_automatically": false,
    "upstream_rights_must_be_preserved": false
  },
  "mesh": {
    "primary_home": null,
    "branch": "migration-residue",
    "subcategory": "unresolved-primary-home",
    "routing": [
      {
        "relation": "estate-map",
        "target": "GlacierEQ/monolith",
        "url": "https://github.com/GlacierEQ/monolith"
      }
    ],
    "boundaries": [
      "routing-does-not-transfer-source-code-evidence-deployment-or-lifecycle-authority",
      "generated-contract-is-a-source-index-not-a-runtime-or-provider-receipt",
      "implementation-and-provider-state-require-independent-evidence",
      "presentation-calibration-cannot-promote-claim-or-evidence-state",
      "license-automation-cannot-relicense-unresolved-upstream-or-third-party-rights"
    ]
  },
  "provenance": {
    "generated_by": "GlacierEQ/job-app-helix",
    "generator_contract": "estate-machine-v1",
    "classification_source": null,
    "classification_evidence_path": null,
    "classification_evidence_blob_sha": null,
    "classification_status": null,
    "contract_digest": "068bd70e7d4a6babd15b67dca5ab6b08f4e672d730e4f3c80a18c8e4da500450"
  }
}
```
<!-- glacier-eq-protocol:end -->
