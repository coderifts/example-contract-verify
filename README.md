# example-contract-verify

A tiny, dependency-free reference for the **verify side** of a discovery and
attestation protocol for AI tool contracts.

An agent fetches a small signed bundle that describes a tool's current API
contract, verifies it, and gets a verdict before any tool code runs. This repo
implements the verify half: signature check, hash pin, freshness, and the
verdict gate. It runs on plain `python3` with no installs.

It is the companion to the protocol sketch:
https://coderifts.com/blog/contract-discovery-attestation-protocol/

The design was worked out in the open. The fetch-flow half (well-known endpoint
plus the signed ref advertisement) is being sketched separately; this is the
verify half, meant to wire together into one reference loop.

## The bundle

A bundle is a small JSON object. The signature covers every field except
`signature`.

```
{
  "ref": "refs/heads/main",
  "commit_sha": "<40 hex>",
  "content_hash": "sha256:<hex>",
  "issued_at": 1000000,
  "ttl_seconds": 300,
  "version": 7,
  "verdict": "PASS",            // PASS | REQUIRE_APPROVAL | BLOCK
  "key_id": "ed25519:guard-ci",
  "signature": "<hex>"
}
```

## The verify pipeline

Order matters:

1. **Signature.** Verify the bundle signature against a trusted guard key.
2. **Hash pin.** `content_hash` must equal `sha256` of the contract bytes.
3. **Freshness.** `ref` matches, `version` is not lower than the last accepted
   version (rollback protection), and the bundle is inside its TTL.
4. **Gate.** Map the verdict to an action: `PASS` allows, `REQUIRE_APPROVAL`
   holds for escalation, `BLOCK` denies. The agent acts on this before calling
   the tool.

Freshness rides on the signed bundle itself, so the agent never walks git
history and makes no extra roundtrips. The version plus TTL is the timestamp
role from TUF, scoped to a single repo, with no central authority.

## Run it

No dependencies. Ed25519 is a small pure-Python implementation in `_ed25519.py`.

```
python3 demo.py
python3 -m unittest -v
```

Expected demo trace:

```
fresh PASS                 | ACCEPT | verdict=PASS             | action=allow | ok
revalidate at v7           | ACCEPT | verdict=PASS             | action=allow | ok
fresh BLOCK                | ACCEPT | verdict=BLOCK            | action=deny  | ok
fresh REQUIRE_APPROVAL     | ACCEPT | verdict=REQUIRE_APPROVAL | action=hold  | ok
tampered contract          | REJECT | verdict=-                | action=-     | hash pin mismatch
rollback to v5             | REJECT | verdict=-                | action=-     | rollback: version 5 < last seen 7
expired (past TTL)         | REJECT | verdict=-                | action=-     | expired: now 1000301 > issued_at+ttl 1000300
wrong ref (dev)            | REJECT | verdict=-                | action=-     | ref mismatch: refs/heads/dev
untrusted signer           | REJECT | verdict=-                | action=-     | signature invalid
```

## What this is, and is not

- This is the **protocol** verify layer. The guard that decides
  `PASS / REQUIRE_APPROVAL / BLOCK` is a black box here. Any guard that emits a
  deterministic, signable verdict fits.
- `issuer.py` is a local signer that stands in for the guard so the example runs
  end to end. In a real deployment the verdict is signed by the guard identity
  in CI: keyless OIDC workload identity, or a guard public key anchored in the
  signed repo so git history is the root of trust.
- Provenance stays with the author commit signature. The verdict is a separate
  signature from the guard. Two roles, two keys.

## Files

- `coderifts_verify.py` verify pipeline and the gate
- `_ed25519.py` dependency-free Ed25519
- `issuer.py` test signer (stands in for the guard in CI)
- `demo.py` end to end, prints the trace, asserts every outcome
- `test_verify.py` unit tests

## License

MIT. See `LICENSE`.
