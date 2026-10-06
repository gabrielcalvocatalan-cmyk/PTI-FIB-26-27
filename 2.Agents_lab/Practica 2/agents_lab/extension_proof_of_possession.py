"""Section 4 extension: proof-of-possession.

So far, verify_capability_credential() (common/identity.py) checks that a
credential is validly signed, issued by the trust anchor, and lists the
right capability. But it never checks that the agent we're actually
talking to over HTTP is the one that credential is about - a malicious
agent could simply copy someone else's did.json and credential.json onto
its own server and claim to be them, since nothing today asks it to prove
it holds the matching PRIVATE key.

Every agent already exposes POST /prove (see common/agent_server.py and
common/identity.py's issue_self_signed_proof): send it a nonce, and it
signs a small self-issued credential over that nonce with its own key.

Your job: complete verify_proof() below so this script correctly tells
apart a real agent from an impersonator.

Run it against a live agent (make sure trust_anchor.py and agent_rental.py
are running first):

    python3 extension_proof_of_possession.py rental-agent
"""
import secrets
import sys

import requests

import common.identity  # noqa: F401 - import for its resolve_did_url patch, see common/identity.py
from pyvckit.verify import verify_signature

import config


def request_proof(base_url: str, nonce: str) -> dict:
    response = requests.post(f"{base_url}/prove", json={"nonce": nonce}, timeout=5)
    response.raise_for_status()
    return response.json()


def verify_proof(proof: dict, claimed_did: str, expected_nonce: str) -> tuple[bool, str]:
    """TODO(student): implement the four checks described in the README
    section 4, reusing verify_capability_credential() in
    common/identity.py as a model. You need:

    1. The proof's signature is cryptographically valid.
       (hint: pyvckit.verify.verify_signature, already imported above)
    2. The proof is self-issued: proof["issuer"]["id"] == claimed_did.
    3. The proof's subject is also claimed_did:
       proof["credentialSubject"]["id"] == claimed_did.
    4. The nonce inside the proof matches the nonce *you* generated:
       proof["credentialSubject"]["nonce"] == expected_nonce.
       (this is what stops an attacker from replaying a proof they
       captured earlier for a different challenge)

    Return (True, "ok") only if all four checks pass; otherwise return
    (False, "<reason>").
    """
    raise NotImplementedError("implement verify_proof()")


def main():
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "rental-agent"
    info = config.AGENTS[agent_name]
    base_url = config.agent_base_url(info)

    card = requests.get(f"{base_url}/.well-known/agent-card.json", timeout=5).json()
    claimed_did = card["securitySchemes"]["didAuth"]["did"]
    print(f"{agent_name} claims to be: {claimed_did}")

    nonce = secrets.token_hex(16)
    print(f"Challenge nonce: {nonce}")

    proof = request_proof(base_url, nonce)
    ok, reason = verify_proof(proof, claimed_did, nonce)

    print(f"\nProof of possession: {'PASS' if ok else 'FAIL'} ({reason})")


if __name__ == "__main__":
    main()
