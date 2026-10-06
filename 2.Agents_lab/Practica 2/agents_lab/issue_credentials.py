"""One-shot script: the trust anchor issues one AgentCapabilityCredential
per agent in config.AGENTS, and writes each signed credential to
credentials/<agent_keys_name>.json.

Run this once, any time after generating the trust anchor's identity
(trust_anchor.py creates it on first run) and before starting the agents:

    python3 issue_credentials.py

Re-run it any time you want to re-issue (e.g. after "breaking" a credential
on purpose to see verification fail, as suggested in the README).
"""
import json
import os

import config
from common.identity import load_or_create_identity, issue_capability_credential


def main():
    ta_did, ta_keys = load_or_create_identity(
        config.TRUST_ANCHOR_KEYS_NAME, config.HOST, config.TRUST_ANCHOR_PORT, config.KEYS_DIR
    )
    print(f"Issuing credentials from trust anchor: {ta_did}\n")

    os.makedirs(config.CREDENTIALS_DIR, exist_ok=True)

    for agent_name, info in config.AGENTS.items():
        agent_did, _ = load_or_create_identity(
            info["keys_name"], info["host"], info["port"], config.KEYS_DIR
        )
        credential = issue_capability_credential(
            issuer_did=ta_did,
            issuer_keys=ta_keys,
            subject_did=agent_did,
            subject_name=agent_name,
            capabilities=[info["capability"]],
        )

        out_path = config.credential_path(info["keys_name"])
        with open(out_path, "w") as f:
            json.dump(credential, f, indent=2)

        print(f"{agent_name}")
        print(f"  DID:        {agent_did}")
        print(f"  capability: {info['capability']}")
        print(f"  credential: {out_path}\n")


if __name__ == "__main__":
    main()
