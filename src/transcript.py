"""Constitutional tool transcript — policy-bound deterministic decisions."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    REFUSE = "REFUSE"


@dataclass(frozen=True)
class Policy:
    policy_id: str
    red_lines: frozenset[str]  # tool names always refused
    allowed_tools: frozenset[str]

    def policy_hash(self) -> str:
        return digest({"id": self.policy_id, "red": sorted(self.red_lines), "allow": sorted(self.allowed_tools)})


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool: str
    args: Mapping[str, Any]


@dataclass(frozen=True)
class TranscriptEntry:
    call_id: str
    verdict: Verdict
    reason: str
    policy_hash: str
    input_digest: str
    fingerprint: str


class ConstitutionalTranscript:
    def __init__(self, policy: Policy):
        self.policy = policy
        self.entries: list[TranscriptEntry] = []

    def decide(self, call: ToolCall) -> TranscriptEntry:
        inp = digest({"tool": call.tool, "args": dict(call.args)})
        if call.tool in self.policy.red_lines:
            verdict, reason = Verdict.REFUSE, "RED_LINE"
        elif call.tool not in self.policy.allowed_tools:
            verdict, reason = Verdict.REFUSE, "NOT_IN_POLICY"
        else:
            verdict, reason = Verdict.ALLOW, "POLICY_ALLOW"
        body = {
            "call": call.call_id,
            "verdict": verdict.value,
            "reason": reason,
            "ph": self.policy.policy_hash(),
            "inp": inp,
        }
        entry = TranscriptEntry(
            call.call_id, verdict, reason, self.policy.policy_hash(), inp, digest(body)
        )
        self.entries.append(entry)
        return entry

    def replay(self, calls: list[ToolCall]) -> list[TranscriptEntry]:
        """Recompute decisions; fingerprints must match prior for same policy+calls."""
        clone = ConstitutionalTranscript(self.policy)
        return [clone.decide(c) for c in calls]
