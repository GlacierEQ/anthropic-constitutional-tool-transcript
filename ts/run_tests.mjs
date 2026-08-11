import assert from "node:assert/strict";
import {
  ConstitutionalTranscript,
  canonicalJson,
  decide,
  policyHash,
  replay,
  verifyReplayReceipt,
} from "./transcript.mjs";

const A = "a".repeat(64);
const B = "b".repeat(64);
const policy = {
  policyId: "p1",
  redLines: new Set(["bash"]),
  allowedTools: new Set(["read_file", "search"]),
  toolSchemas: {
    search: { tool: "search", version: "v1", schemaDigest: A },
    read_file: { tool: "read_file", version: "v2", schemaDigest: B },
  },
};

const red = decide(policy, { callId: "red", tool: "bash", args: {} });
assert.equal(red.verdict, "REFUSE");
assert.equal(red.reason, "RED_LINE");

const tx = new ConstitutionalTranscript(policy);
const allowed = tx.decide({ callId: "c1", tool: "search", args: { q: "a" }, schemaVersion: "v1" });
assert.equal(allowed.verdict, "ALLOW");
assert.equal(allowed.reason, "POLICY_ALLOW");
assert.equal(allowed.schemaDigest, A);

const mismatch = new ConstitutionalTranscript(policy).decide({
  callId: "c2", tool: "search", args: { q: "a" }, schemaVersion: "v2",
});
assert.equal(mismatch.verdict, "REFUSE");
assert.equal(mismatch.reason, "SCHEMA_VERSION_MISMATCH");

const unboundPolicy = {
  policyId: "p2",
  redLines: new Set(),
  allowedTools: new Set(["search"]),
};
const unbound = decide(unboundPolicy, { callId: "c1", tool: "search", args: {}, schemaVersion: "v1" });
assert.equal(unbound.reason, "SCHEMA_UNBOUND");

const oneShot = new ConstitutionalTranscript(policy);
const exactCall = { callId: "once", tool: "search", args: { q: "same" }, schemaVersion: "v1" };
const first = oneShot.decide(exactCall);
const second = oneShot.decide(exactCall);
assert.deepEqual(first, second);
assert.equal(oneShot.entries.length, 1);
assert.throws(
  () => oneShot.decide({ ...exactCall, args: { q: "changed" } }),
  /CALL_ID_REBOUND/,
);
assert.equal(oneShot.entries.length, 1);

const argA = decide(policy, { callId: "arg", tool: "search", args: { q: "alpha" }, schemaVersion: "v1" });
const argB = decide(policy, { callId: "arg", tool: "search", args: { q: "beta" }, schemaVersion: "v1" });
assert.notEqual(argA.inputDigest, argB.inputDigest);
assert.notEqual(argA.fingerprint, argB.fingerprint);

const orderedA = decide(policy, {
  callId: "ordered", tool: "search", args: { q: "alpha", limit: 3 }, schemaVersion: "v1",
});
const orderedB = decide(policy, {
  callId: "ordered", tool: "search", args: { limit: 3, q: "alpha" }, schemaVersion: "v1",
});
assert.equal(orderedA.inputDigest, orderedB.inputDigest);
assert.equal(orderedA.fingerprint, orderedB.fingerprint);
assert.equal(canonicalJson({ z: { b: 2, a: 1 }, a: 0 }), '{"a":0,"z":{"a":1,"b":2}}');

const chain = new ConstitutionalTranscript(policy);
const chainA = chain.decide({ callId: "a", tool: "search", args: { q: "a" }, schemaVersion: "v1" });
const chainB = chain.decide({ callId: "b", tool: "read_file", args: { path: "x" }, schemaVersion: "v2" });
assert.equal(chainB.sequence, 1);
assert.equal(chainB.prevFingerprint, chainA.fingerprint);
const reversed = new ConstitutionalTranscript(policy);
reversed.decide({ callId: "b", tool: "read_file", args: { path: "x" }, schemaVersion: "v2" });
const reversedSecond = reversed.decide({ callId: "a", tool: "search", args: { q: "a" }, schemaVersion: "v1" });
assert.notEqual(chainB.fingerprint, reversedSecond.fingerprint);

const calls = [
  { callId: "r1", tool: "search", args: { q: "a" }, schemaVersion: "v1" },
  { callId: "r2", tool: "bash", args: { cmd: "rm" } },
];
const receipt = new ConstitutionalTranscript(policy).makeReplayReceipt(calls);
assert.equal(verifyReplayReceipt(policy, calls, receipt), true);
assert.equal(
  verifyReplayReceipt(policy, [{ ...calls[0], args: { q: "tampered" } }, calls[1]], receipt),
  false,
);
assert.equal(verifyReplayReceipt(policy, [...calls].reverse(), receipt), false);

const duplicateReceipt = new ConstitutionalTranscript(policy).makeReplayReceipt([exactCall, exactCall]);
assert.equal(duplicateReceipt.requestedCallCount, 2);
assert.equal(duplicateReceipt.uniqueEntryCount, 1);
assert.equal(verifyReplayReceipt(policy, [exactCall, exactCall], duplicateReceipt), true);

const changedPolicy = {
  ...policy,
  toolSchemas: {
    ...policy.toolSchemas,
    search: { tool: "search", version: "v9", schemaDigest: A },
  },
};
assert.notEqual(policyHash(policy), policyHash(changedPolicy));

assert.throws(
  () => decide(policy, { callId: "nan", tool: "search", args: { score: Number.NaN }, schemaVersion: "v1" }),
  /non_finite_json/,
);
assert.throws(
  () => decide(policy, { callId: "date", tool: "search", args: { when: new Date() }, schemaVersion: "v1" }),
  /unsupported_json_value/,
);

// Cross-runtime fixed vector: Python tests assert the same policy, input, entry, and receipt hashes.
assert.equal(policyHash(policy), "075dd3ae76e93ef50bdf66c30fc13460a670862d2feac498c70acc0e7db3054b");
const vectorCall = { callId: "c1", tool: "search", args: { limit: 3, q: "alpha" }, schemaVersion: "v1" };
const vectorEntry = decide(policy, vectorCall);
assert.equal(vectorEntry.inputDigest, "ff5d94363ebe944a5c358837999adc932ba2607d24d9f4bb1dee5cb797b7058a");
assert.equal(vectorEntry.fingerprint, "36670378e869a7b117b2e936c8667729a6a922aab00769aeba29789c7bfc2e99");
const vectorReceipt = new ConstitutionalTranscript(policy).makeReplayReceipt([vectorCall]);
assert.equal(vectorReceipt.fingerprint, "4046d428ce97bbac5fb6d7baaf9b1a7cdd55ffd1fa4be0753696f7a79030d61d");

const replayA = replay(policy, calls);
const replayB = replay(policy, calls);
assert.deepEqual(replayA.map(x => x.fingerprint), replayB.map(x => x.fingerprint));

console.log("ok");
