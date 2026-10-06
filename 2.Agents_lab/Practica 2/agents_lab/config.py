"""Shared configuration: ports, file locations, and the agent registry.

Every script in this lab (trust_anchor.py, issue_credentials.py, the three
agent processes, agent_orchestrator.py) imports this module so there is a
single place that defines who runs where, and what each agent is allowed
to do.
"""
import os

HOST = "localhost"

TRUST_ANCHOR_PORT = 8100
AGENT_RENTAL_PORT = 8101
AGENT_RAG_PORT = 8102
ORCHESTRATOR_PORT = 8103

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_DIR = os.path.join(BASE_DIR, "keys")
CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")

TRUST_ANCHOR_KEYS_NAME = "trust_anchor"

# The agent registry: this is the closest thing this lab has to a
# "discovery service" - in a real deployment agents might discover each
# other through a directory service instead of a shared config file.
AGENTS = {
    "rental-agent": {
        "host": HOST,
        "port": AGENT_RENTAL_PORT,
        "keys_name": "agent_rental",
        "capability": "list_rentals",
    },
    "rag-agent": {
        "host": HOST,
        "port": AGENT_RAG_PORT,
        "keys_name": "agent_rag",
        "capability": "rag_query",
    },
}


def agent_base_url(agent_info: dict) -> str:
    return f"http://{agent_info['host']}:{agent_info['port']}"


def credential_path(keys_name: str) -> str:
    return os.path.join(CREDENTIALS_DIR, f"{keys_name}.json")


def trust_anchor_did() -> str:
    """Load (or create, if this is the very first script run) the trust
    anchor's identity and return just its DID."""
    from common.identity import load_or_create_identity

    did, _ = load_or_create_identity(TRUST_ANCHOR_KEYS_NAME, HOST, TRUST_ANCHOR_PORT, KEYS_DIR)
    return did
