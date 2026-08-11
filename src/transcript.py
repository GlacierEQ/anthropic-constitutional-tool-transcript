"""Constitutional tool transcript — schema-bound deterministic decision receipts."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


_HEX = frozenset("0123456789abcdef")
_GENESIS = "0" * 64


def _validate_token(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name)
    return value


def _validate_digest(name: str, value: str) -> str:
    _validate_token(name, value)
    if len(value) != 64 or any(ch not in _HEX for ch in value):
        raise ValueError(name)
    return value


def _strict_json_value(value: Any, path: str = "$") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non_finite_json:{path}")
        return value
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non_string_json_key:{path}")
            normalized[key] = _strict_json_value(item, f"{path}.{key}")
        return normalized
    if isinstance(value, (list, tuple)):
        return [_strict_json_value(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise TypeError(f"unsupported_json_value:{path}:{type(value).__name__}")


def canonical_json(obj: Any) -> str:
    normalized = _strict_json_value(obj)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    REFUSE = "REFUSE"


@dataclass(frozen=True)
class ToolSchemaRef:
    tool: str
    version: str
    schema_digest: str

    def __post_init__(self) -> None:
        _validate_token("schema_tool", self.tool)
        _validate_token("schema_version", self.version)
        _validate_digest("schema_digest", self.schema_digest)

    def body(self) -> dict[str, str]:
        return {
            "tool": self.tool,
            "version": self.version,
            "digest": self.schema_digest,
        }


@dataclass(frozen=True)
class Policy:
    policy_id: str
    red_lines: frozenset[str]
    allowed_tools: frozenset[str]
    tool_schemas: Mapping[str, ToolSchemaRef] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_token("policy_id", self.policy_id)
        for tool in self.red_lines | self.allowed_tools:
            _validate_token("tool", tool)
        for key, schema in self.tool_schemas.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("schema_key")
            if not isinstance(schema, ToolSchemaRef):
                raise TypeError("tool_schema")
            if key != schema.tool:
                raise ValueError("schema_tool_mismatch")
            if key not in self.red_lines and key not in self.allowed_tools:
                raise ValueError("schema_for_undeclared_tool")

    def policy_hash(self) -> str:
        return digest(
            {
                "id": self.policy_id,
                "red": sorted(self.red_lines),
                "allow": sorted(self.allowed_tools),
                "schemas": [self.tool_schemas[name].body() for name in sorted(self.tool_schemas)],
            }
        )


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool: str
    args: Mapping[str, Any]
    schema_version: str = ""

    def __post_init__(self) -> None:
        _validate_token("call_id", self.call_id)
        _validate_token("tool", self.tool)
        if not isinstance(self.schema_version, str):
            raise TypeError("schema_version")
        if not isinstance(self.args, Mapping):
            raise TypeError("args")
        # Validate at construction so malformed evidence never reaches policy evaluation.
        _strict_json_value(self.args, "$.args")

    def input_body(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "args": dict(self.args),
            "schema_version": self.schema_version,
        }

    def input_digest(self) -> str:
        return digest(self.input_body())

    def receipt_body(self) -> dict[str, Any]:
        return {"call_id": self.call_id, **self.input_body()}


@dataclass(frozen=True)
class TranscriptEntry:
    call_id: str
    tool: str
    schema_version: str
    schema_digest: str
    verdict: Verdict
    reason: str
    policy_hash: str
    input_digest: str
    sequence: int
    prev_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class ReplayReceipt:
    policy_hash: str
    call_digest: str
    requested_call_count: int
    unique_entry_count: int
    transcript_root: str
    fingerprint: str


class ConstitutionalTranscript:
    """Fail-closed policy transcript with one-shot call identity and hash chaining."""

    def __init__(self, policy: Policy):
        if not isinstance(policy, Policy):
            raise TypeError("policy")
        self.policy = policy
        self.entries: list[TranscriptEntry] = []
        self._by_call_id: dict[str, tuple[str, TranscriptEntry]] = {}

    def _verdict(self, call: ToolCall) -> tuple[Verdict, str, str]:
        schema = self.policy.tool_schemas.get(call.tool)
        schema_digest = schema.schema_digest if schema is not None else ""
        # Constitutional red lines dominate schema state and never become ALLOW.
        if call.tool in self.policy.red_lines:
            return Verdict.REFUSE, "RED_LINE", schema_digest
        if call.tool not in self.policy.allowed_tools:
            return Verdict.REFUSE, "NOT_IN_POLICY", schema_digest
        if schema is None:
            return Verdict.REFUSE, "SCHEMA_UNBOUND", ""
        if call.schema_version != schema.version:
            return Verdict.REFUSE, "SCHEMA_VERSION_MISMATCH", schema.schema_digest
        return Verdict.ALLOW, "POLICY_ALLOW", schema.schema_digest

    def decide(self, call: ToolCall) -> TranscriptEntry:
        if not isinstance(call, ToolCall):
            raise TypeError("call")
        input_digest = call.input_digest()
        previous = self._by_call_id.get(call.call_id)
        if previous is not None:
            prior_input_digest, prior_entry = previous
            if prior_input_digest != input_digest:
                raise ValueError("CALL_ID_REBOUND")
            return prior_entry

        verdict, reason, schema_digest = self._verdict(call)
        policy_hash = self.policy.policy_hash()
        sequence = len(self.entries)
        prev_fingerprint = self.entries[-1].fingerprint if self.entries else _GENESIS
        body = {
            "call_id": call.call_id,
            "tool": call.tool,
            "schema_version": call.schema_version,
            "schema_digest": schema_digest,
            "verdict": verdict.value,
            "reason": reason,
            "policy_hash": policy_hash,
            "input_digest": input_digest,
            "sequence": sequence,
            "prev_fingerprint": prev_fingerprint,
        }
        entry = TranscriptEntry(
            call_id=call.call_id,
            tool=call.tool,
            schema_version=call.schema_version,
            schema_digest=schema_digest,
            verdict=verdict,
            reason=reason,
            policy_hash=policy_hash,
            input_digest=input_digest,
            sequence=sequence,
            prev_fingerprint=prev_fingerprint,
            fingerprint=digest(body),
        )
        self.entries.append(entry)
        self._by_call_id[call.call_id] = (input_digest, entry)
        return entry

    def replay(self, calls: Sequence[ToolCall]) -> list[TranscriptEntry]:
        """Recompute decisions in a fresh transcript under the same policy."""
        clone = ConstitutionalTranscript(self.policy)
        return [clone.decide(call) for call in calls]

    def make_replay_receipt(self, calls: Sequence[ToolCall]) -> ReplayReceipt:
        clone = ConstitutionalTranscript(self.policy)
        requested = list(calls)
        for call in requested:
            clone.decide(call)
        call_digest = digest([call.receipt_body() for call in requested])
        transcript_root = clone.entries[-1].fingerprint if clone.entries else _GENESIS
        body = {
            "policy_hash": self.policy.policy_hash(),
            "call_digest": call_digest,
            "requested_call_count": len(requested),
            "unique_entry_count": len(clone.entries),
            "transcript_root": transcript_root,
        }
        return ReplayReceipt(
            policy_hash=body["policy_hash"],
            call_digest=call_digest,
            requested_call_count=len(requested),
            unique_entry_count=len(clone.entries),
            transcript_root=transcript_root,
            fingerprint=digest(body),
        )


def verify_replay_receipt(
    policy: Policy,
    calls: Sequence[ToolCall],
    receipt: ReplayReceipt,
) -> bool:
    """Verify a deterministic replay receipt by recomputation; no signer is implied."""
    if not isinstance(receipt, ReplayReceipt):
        return False
    try:
        expected = ConstitutionalTranscript(policy).make_replay_receipt(calls)
    except (TypeError, ValueError):
        return False
    return expected == receipt
