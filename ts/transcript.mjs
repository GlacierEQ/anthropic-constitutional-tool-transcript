import crypto from "node:crypto";

const GENESIS = "0".repeat(64);
const HEX64 = /^[0-9a-f]{64}$/;

function token(name, value) {
  if (typeof value !== "string" || value.trim() === "") throw new TypeError(name);
  return value;
}

function strictValue(value, path = "$") {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError(`non_finite_json:${path}`);
    return value;
  }
  if (Array.isArray(value)) return value.map((item, index) => strictValue(item, `${path}[${index}]`));
  if (typeof value === "object") {
    const proto = Object.getPrototypeOf(value);
    if (proto !== Object.prototype && proto !== null) throw new TypeError(`unsupported_json_value:${path}`);
    const out = {};
    for (const key of Object.keys(value).sort()) out[key] = strictValue(value[key], `${path}.${key}`);
    return out;
  }
  throw new TypeError(`unsupported_json_value:${path}`);
}

export function canonicalJson(value) {
  return JSON.stringify(strictValue(value));
}

export function digest(value) {
  return crypto.createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
}

function schemaEntries(policy) {
  const source = policy.toolSchemas ?? {};
  const entries = source instanceof Map ? [...source.entries()] : Object.entries(source);
  return entries
    .map(([key, schema]) => {
      token("schema_key", key);
      if (!schema || typeof schema !== "object") throw new TypeError("tool_schema");
      const tool = token("schema_tool", schema.tool);
      const version = token("schema_version", schema.version);
      const schemaDigest = token("schema_digest", schema.schemaDigest ?? schema.digest);
      if (!HEX64.test(schemaDigest)) throw new TypeError("schema_digest");
      if (tool !== key) throw new TypeError("schema_tool_mismatch");
      return [key, { tool, version, digest: schemaDigest }];
    })
    .sort(([a], [b]) => a.localeCompare(b));
}

function normalizePolicy(policy) {
  if (!policy || typeof policy !== "object") throw new TypeError("policy");
  const policyId = token("policy_id", policy.policyId);
  if (!(policy.redLines instanceof Set) || !(policy.allowedTools instanceof Set)) throw new TypeError("policy_sets");
  const red = [...policy.redLines].map(value => token("tool", value)).sort();
  const allow = [...policy.allowedTools].map(value => token("tool", value)).sort();
  const declared = new Set([...red, ...allow]);
  const schemas = schemaEntries(policy);
  for (const [key] of schemas) if (!declared.has(key)) throw new TypeError("schema_for_undeclared_tool");
  return { id: policyId, red, allow, schemas: schemas.map(([, schema]) => schema) };
}

export function policyHash(policy) {
  return digest(normalizePolicy(policy));
}

function schemaFor(policy, tool) {
  const source = policy.toolSchemas ?? {};
  if (source instanceof Map) return source.get(tool) ?? null;
  return Object.prototype.hasOwnProperty.call(source, tool) ? source[tool] : null;
}

function normalizeCall(call) {
  if (!call || typeof call !== "object") throw new TypeError("call");
  const callId = token("call_id", call.callId);
  const tool = token("tool", call.tool);
  const schemaVersion = call.schemaVersion ?? "";
  if (typeof schemaVersion !== "string") throw new TypeError("schema_version");
  if (!call.args || typeof call.args !== "object" || Array.isArray(call.args)) throw new TypeError("args");
  const args = strictValue(call.args, "$.args");
  return { callId, tool, args, schemaVersion };
}

function inputBody(call) {
  return { tool: call.tool, args: call.args, schema_version: call.schemaVersion };
}

function receiptCallBody(call) {
  return { call_id: call.callId, ...inputBody(call) };
}

function verdictFor(policy, call) {
  const schema = schemaFor(policy, call.tool);
  const schemaDigest = schema ? (schema.schemaDigest ?? schema.digest ?? "") : "";
  if (policy.redLines.has(call.tool)) return { verdict: "REFUSE", reason: "RED_LINE", schemaDigest };
  if (!policy.allowedTools.has(call.tool)) return { verdict: "REFUSE", reason: "NOT_IN_POLICY", schemaDigest };
  if (!schema) return { verdict: "REFUSE", reason: "SCHEMA_UNBOUND", schemaDigest: "" };
  token("schema_version", schema.version);
  token("schema_digest", schemaDigest);
  if (!HEX64.test(schemaDigest)) throw new TypeError("schema_digest");
  if (call.schemaVersion !== schema.version) return { verdict: "REFUSE", reason: "SCHEMA_VERSION_MISMATCH", schemaDigest };
  return { verdict: "ALLOW", reason: "POLICY_ALLOW", schemaDigest };
}

export class ConstitutionalTranscript {
  constructor(policy) {
    normalizePolicy(policy);
    this.policy = policy;
    this.entries = [];
    this.byCallId = new Map();
  }

  decide(rawCall) {
    const call = normalizeCall(rawCall);
    const inp = digest(inputBody(call));
    const previous = this.byCallId.get(call.callId);
    if (previous) {
      if (previous.inputDigest !== inp) throw new Error("CALL_ID_REBOUND");
      return previous.entry;
    }

    const { verdict, reason, schemaDigest } = verdictFor(this.policy, call);
    const ph = policyHash(this.policy);
    const sequence = this.entries.length;
    const prevFingerprint = sequence ? this.entries[sequence - 1].fingerprint : GENESIS;
    const body = {
      call_id: call.callId,
      tool: call.tool,
      schema_version: call.schemaVersion,
      schema_digest: schemaDigest,
      verdict,
      reason,
      policy_hash: ph,
      input_digest: inp,
      sequence,
      prev_fingerprint: prevFingerprint,
    };
    const entry = {
      callId: call.callId,
      tool: call.tool,
      schemaVersion: call.schemaVersion,
      schemaDigest,
      verdict,
      reason,
      policyHash: ph,
      inputDigest: inp,
      sequence,
      prevFingerprint,
      fingerprint: digest(body),
    };
    this.entries.push(entry);
    this.byCallId.set(call.callId, { inputDigest: inp, entry });
    return entry;
  }

  replay(calls) {
    const clone = new ConstitutionalTranscript(this.policy);
    return [...calls].map(call => clone.decide(call));
  }

  makeReplayReceipt(calls) {
    const requested = [...calls].map(normalizeCall);
    const clone = new ConstitutionalTranscript(this.policy);
    for (const call of requested) clone.decide(call);
    const callDigest = digest(requested.map(receiptCallBody));
    const transcriptRoot = clone.entries.length ? clone.entries.at(-1).fingerprint : GENESIS;
    const body = {
      policy_hash: policyHash(this.policy),
      call_digest: callDigest,
      requested_call_count: requested.length,
      unique_entry_count: clone.entries.length,
      transcript_root: transcriptRoot,
    };
    return {
      policyHash: body.policy_hash,
      callDigest,
      requestedCallCount: requested.length,
      uniqueEntryCount: clone.entries.length,
      transcriptRoot,
      fingerprint: digest(body),
    };
  }
}

export function verifyReplayReceipt(policy, calls, receipt) {
  if (!receipt || typeof receipt !== "object") return false;
  try {
    const expected = new ConstitutionalTranscript(policy).makeReplayReceipt(calls);
    return canonicalJson(expected) === canonicalJson(receipt);
  } catch {
    return false;
  }
}

// Compatibility helpers remain deterministic, but one-shot identity is meaningful only
// when callers retain a ConstitutionalTranscript instance across decisions.
export function decide(policy, call) {
  return new ConstitutionalTranscript(policy).decide(call);
}

export function replay(policy, calls) {
  return new ConstitutionalTranscript(policy).replay(calls);
}
