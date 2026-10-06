"""Shared Flask scaffolding for the capability agents (agent_rental.py,
agent_rag.py). Both agents need the exact same four routes - only what
happens inside /invoke differs - so that boilerplate lives here once and
each agent script just supplies its capability handler.
"""
import json

from flask import Flask, Response, jsonify, request

import config
from common.identity import (
    load_or_create_identity,
    did_document_json,
    did_document_route,
    issue_self_signed_proof,
)


def build_agent(name: str, skill_name: str, skill_description: str, parameters: dict, handler):
    """
    name: key into config.AGENTS, e.g. "rental-agent" - also used as the
        agent's display name and as its single skill id (config.AGENTS[name]
        already records the one capability this agent offers).
    parameters: JSON Schema for the skill's args, published in the agent
        card so the orchestrator can build an Ollama tool definition purely
        from discovery, without hardcoding it anywhere else.
    handler: callable(args: dict) -> JSON-serializable result
    """
    info = config.AGENTS[name]
    skill_id = info["capability"]
    did, keys = load_or_create_identity(info["keys_name"], info["host"], info["port"], config.KEYS_DIR)
    did_route = did_document_route(did)

    credential_file = config.credential_path(info["keys_name"])

    app = Flask(name)

    @app.get(did_route)
    def serve_did_document():
        return Response(did_document_json(did, keys), mimetype="application/json")

    @app.get("/.well-known/agent-card.json")
    def serve_agent_card():
        return jsonify({
            "protocolVersion": "0.3.0",
            "name": name,
            "description": skill_description,
            "url": config.agent_base_url(info) + "/",
            "preferredTransport": "HTTP+JSON",
            "capabilities": {"streaming": False, "pushNotifications": False},
            "securitySchemes": {"didAuth": {"type": "did", "did": did}},
            "skills": [
                {
                    "id": skill_id,
                    "name": skill_name,
                    "description": skill_description,
                    "parameters": parameters,
                }
            ],
        })

    @app.get("/credential.json")
    def serve_credential():
        try:
            with open(credential_file) as f:
                return jsonify(json.load(f))
        except FileNotFoundError:
            return jsonify({"error": "no credential issued yet - run issue_credentials.py"}), 404

    @app.post("/invoke")
    def invoke():
        body = request.get_json(force=True) or {}
        capability = body.get("capability")
        args = body.get("args", {})
        if capability != skill_id:
            return jsonify({"error": f"unknown capability {capability!r}, this agent only offers {skill_id!r}"}), 400
        result = handler(args)
        return jsonify({"result": result, "agent_id": did})

    @app.post("/prove")
    def prove():
        """Section 4 (proof-of-possession extension): sign whatever nonce
        the caller sends with our own key, proving we actually control the
        private key behind our DID rather than just asserting it."""
        body = request.get_json(force=True) or {}
        nonce = body.get("nonce", "")
        return jsonify(issue_self_signed_proof(did, keys, nonce))

    return app, did
