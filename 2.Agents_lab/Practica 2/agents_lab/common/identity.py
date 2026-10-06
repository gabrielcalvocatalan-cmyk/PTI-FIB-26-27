"""Shared DID / Verifiable Credential helper built on pyvckit.

Every process in this lab (the trust anchor and the three agents) uses the
same few functions here to: create a did:web identity, serve its DID
document, issue a capability credential (trust anchor only), and verify a
credential presented by a peer (agents / orchestrator).

Two local-dev quirks worth explaining to students (see the README):
1. pyvckit's resolve_did_url() builds the did:web resolution URL from the
   DID string without percent-decoding the domain component, so a
   did:web identity that includes a port (e.g. did:web:localhost%3A8101:...)
   resolves to the literal, unusable hostname "localhost%3A8101" instead
   of "localhost:8101". _patch_resolve_did_url(), called once at import
   time below, fixes this. Same category of localhost-only workaround
   idhub itself needs (see idhub/idhub/apps.py's _patch_pyvckit_loader).
2. This pyvckit variant never resolves to /.well-known/did.json - it
   always treats the DID's own multibase hash suffix as a URL path
   segment too. did_document_route() below derives the correct path to
   serve at, rather than assuming .well-known.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit, urlunsplit

import pyvckit.did as _pv_did
from pyvckit.did import generate_keys, generate_did, gen_did_document
from pyvckit.sign import sign
from pyvckit.verify import verify_signature

# pyvckit signs the URDNA2015-normalized RDF graph of the credential, which
# is produced by JSON-LD expanding it against its own "@context". The
# standard VC 2.0 context (https://www.w3.org/ns/credentials/v2) has no term
# mapping for our own fields (name, capabilities, nonce, ...), and JSON-LD
# expansion silently *drops* any term with no mapping - so without this
# "@vocab" fallback, those fields would never actually be covered by the
# signature at all, and tampering with them would go undetected.
LAB_CONTEXT = [
    "https://www.w3.org/ns/credentials/v2",
    {"@vocab": "https://agents-lab.pti.example/vocab#"},
]


def _patch_resolve_did_url():
    original = _pv_did.resolve_did_url

    def patched(did):
        url = original(did)
        if url is None:
            return None
        parts = urlsplit(url)
        return urlunsplit(
            (parts.scheme, unquote(parts.netloc), parts.path, parts.query, parts.fragment)
        )

    _pv_did.resolve_did_url = patched


_patch_resolve_did_url()


def web_base_url(host: str, port: int) -> str:
    """Base URL to hand to generate_did() so the resulting did:web survives
    the round trip through resolve_did_url() (see module docstring)."""
    return f"http://{host}%3A{port}"


def load_or_create_identity(name: str, host: str, port: int, keys_dir: str = "."):
    """Return (did, keys_dict) for `name`. Generates and persists a new
    Ed25519 keypair + did:web identity the first time it's called; loads the
    same identity from disk on every later call."""
    os.makedirs(keys_dir, exist_ok=True)
    keys_path = os.path.join(keys_dir, f"{name}_keys.json")
    base_url = web_base_url(host, port)

    if os.path.exists(keys_path):
        with open(keys_path) as f:
            keys = json.load(f)
        did = generate_did(json.dumps(keys), base_url)
        return did, keys

    key_material = generate_keys()
    did = generate_did(key_material, base_url)
    keys = json.loads(key_material)

    with open(keys_path, "w") as f:
        json.dump(keys, f, indent=2)

    return did, keys


def did_document_json(did: str, keys: dict) -> str:
    """The did.json document body itself."""
    _, document = gen_did_document(did, keys)
    return document


def did_document_route(did: str) -> str:
    """The URL path this DID's document must be served at for
    pyvckit.did.resolve_did() to find it.

    This pyvckit did:web variant does *not* resolve to
    /.well-known/did.json: generate_did() always appends the key's
    multibase hash as a trailing DID segment (see key_to_did() in
    pyvckit/did.py), and resolve_did_url() in turn always treats that
    segment as a URL *path* component, e.g. did:web:localhost%3A8101:z6Mk...
    resolves to http://localhost:8101/z6Mk.../did.json - not
    .../.well-known/did.json. We ask resolve_did_url() directly (rather
    than re-deriving the same parsing rules ourselves) so this can never
    drift out of sync with how resolution actually works.
    """
    resolution_url = _pv_did.resolve_did_url(did)
    return urlsplit(resolution_url).path


def issue_capability_credential(issuer_did, issuer_keys, subject_did, subject_name, capabilities):
    """Trust anchor issues an AgentCapabilityCredential VC to one agent."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    credential = {
        "@context": LAB_CONTEXT,
        "id": f"urn:uuid:{uuid.uuid4()}",
        "type": ["VerifiableCredential", "AgentCapabilityCredential"],
        "issuer": {"id": issuer_did},
        "validFrom": now,
        "credentialSubject": {
            "id": subject_did,
            "name": subject_name,
            "capabilities": capabilities,
        },
    }
    return sign(json.dumps(credential), json.dumps(issuer_keys), issuer_did)


def issue_self_signed_proof(did: str, keys: dict, nonce: str) -> dict:
    """An agent signs a challenge nonce with its own key, to prove it
    controls the private key behind its DID - not just that it can assert
    the DID string in an agent card or a VC it happens to be holding. Used
    by the section 4 proof-of-possession extension.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    proof_doc = {
        "@context": LAB_CONTEXT,
        "id": f"urn:uuid:{uuid.uuid4()}",
        "type": ["VerifiableCredential", "PossessionProof"],
        "issuer": {"id": did},
        "validFrom": now,
        "credentialSubject": {"id": did, "nonce": nonce},
    }
    return sign(json.dumps(proof_doc), json.dumps(keys), did)


def verify_capability_credential(vc: dict, expected_subject_did: str, required_capability: str,
                                  trusted_issuer_did: str):
    """The trust check a peer's VC must pass before we call it.

    Returns (ok: bool, reason: str). Checks, in order: cryptographic
    signature validity (resolves the issuer's did:web), that the issuer is
    the trust anchor we're configured to trust, that the credential's
    subject DID matches the DID the calling agent actually claims, and that
    the requested capability is listed.
    """
    ok, message = verify_signature(vc)
    if not ok:
        return False, f"signature invalid: {message}"

    issuer_id = (vc.get("issuer") or {}).get("id")
    if issuer_id != trusted_issuer_did:
        return False, f"untrusted issuer: {issuer_id!r} (expected {trusted_issuer_did!r})"

    subject = vc.get("credentialSubject") or {}
    if subject.get("id") != expected_subject_did:
        return False, (
            f"subject DID mismatch: credential is for {subject.get('id')!r}, "
            f"but agent claims {expected_subject_did!r}"
        )

    if required_capability not in subject.get("capabilities", []):
        return False, f"credential does not list capability {required_capability!r}"

    return True, "ok"
