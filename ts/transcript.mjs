import crypto from "node:crypto";
function digest(obj) {
  return crypto.createHash("sha256").update(JSON.stringify(obj)).digest("hex");
}
export function decide(policy, call) {
  const ph = digest({ id: policy.policyId, red: [...policy.redLines].sort(), allow: [...policy.allowedTools].sort() });
  let verdict = "ALLOW", reason = "POLICY_ALLOW";
  if (policy.redLines.has(call.tool)) { verdict = "REFUSE"; reason = "RED_LINE"; }
  else if (!policy.allowedTools.has(call.tool)) { verdict = "REFUSE"; reason = "NOT_IN_POLICY"; }
  return { callId: call.callId, verdict, reason, policyHash: ph, fingerprint: digest({ callId: call.callId, verdict, reason, ph }) };
}
export function replay(policy, calls) {
  return calls.map(c => decide(policy, c));
}
