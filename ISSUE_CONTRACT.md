# ISSUE CONTRACT

## Pain
A policy decision transcript is not reliable proof if tool arguments are omitted from identity, call IDs can be rebound, tool schemas are implicit, or replay has no independently recomputable receipt.

## Success
- Red-line tools always fail closed with a stable refusal reason.
- Allowed decisions require the policy-bound tool schema version and schema digest.
- One call ID binds one immutable tool/schema/argument input; exact replay is idempotent and rebinding is rejected.
- Transcript entries bind policy, input, sequence, and prior entry through a deterministic hash chain.
- Replay receipts bind ordered calls and transcript root and verify by independent recomputation.
- Python and Node preserve fixed cross-runtime identity vectors.
- Non-finite or unsupported evidence fails closed.

## Boundaries
- Replay receipts are deterministic hashes, not cryptographic signatures.
- Schema digests are policy-supplied references, not authenticated registry attestations.
- The transcript does not execute tools or verify tool results.
- No Anthropic affiliation, adoption, or production safety-service claim.
