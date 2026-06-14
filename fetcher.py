"""
fetcher: the minimal reference fetch side of the loop.

It does one GET against a tool's well-known endpoint and returns the signed
bundle plus the contract bytes. Stdlib only (urllib), no external deps. This
pairs directly with verify_bundle in coderifts_verify.

The well-known document is a small JSON object:
    { "bundle": { ...signed bundle... }, "contract": "<contract text>" }

In a real deployment the contract may already be held by hash (steady state),
in which case only the bundle is refetched. This minimal version fetches both
in one request to keep the cold-start path a single round trip.
"""

import json
import urllib.request

WELL_KNOWN_PATH = "/.well-known/contract"


def fetch(base_url, timeout=5):
    """GET base_url + /.well-known/contract and return (bundle, contract_bytes)."""
    url = base_url.rstrip("/") + WELL_KNOWN_PATH
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        doc = json.loads(resp.read().decode("utf-8"))
    bundle = doc["bundle"]
    contract_bytes = doc["contract"].encode("utf-8")
    return bundle, contract_bytes
