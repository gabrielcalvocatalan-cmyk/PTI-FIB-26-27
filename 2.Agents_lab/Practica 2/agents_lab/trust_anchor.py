"""The trust anchor: the one identity every agent and the orchestrator is
configured to trust. It doesn't do anything except exist and prove it
controls its own DID by serving its DID document.

Run this first, and leave it running in its own terminal for the whole lab
session - every credential verification needs to resolve this DID over
HTTP.

    python3 trust_anchor.py
"""
from flask import Flask, Response

import config
from common.identity import load_or_create_identity, did_document_json, did_document_route

app = Flask(__name__)

did, keys = load_or_create_identity(
    config.TRUST_ANCHOR_KEYS_NAME, config.HOST, config.TRUST_ANCHOR_PORT, config.KEYS_DIR
)
did_route = did_document_route(did)


@app.get(did_route)
def serve_did_document():
    return Response(did_document_json(did, keys), mimetype="application/json")


if __name__ == "__main__":
    print(f"Trust anchor DID: {did}")
    print(f"Serving did.json at http://{config.HOST}:{config.TRUST_ANCHOR_PORT}{did_route}")
    app.run(host="0.0.0.0", port=config.TRUST_ANCHOR_PORT)
