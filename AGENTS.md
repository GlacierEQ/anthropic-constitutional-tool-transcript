# AGENTS

## Epistemology / Verification

- Tests: Python 26/26 passing (`PYTHONPATH=src pytest tests/ -v`); Node suite passing (`node ts/run_tests.mjs`).
- Lint: `ruff check src/ tests/` clean.
- L0/L1/L2: presence, structure, and behavior verified as above.
- Aspirational (L0/L1 only): authenticated schema registry, tool-result receipts, tool execution verification, cryptographic signatures, production deployment.

## Verified test suite

- `tests/test_transcript.py` — 13 tests
- `tests/test_promotion_authority.py` — 3 tests
- `tests/test_adversarial.py` — 3 tests
- `tests/test_canonical_position_contract.py` — 4 tests
- `tests/test_evolution_contract.py` — 3 tests
- Total: 26 passed (Python), Node suite passed.
