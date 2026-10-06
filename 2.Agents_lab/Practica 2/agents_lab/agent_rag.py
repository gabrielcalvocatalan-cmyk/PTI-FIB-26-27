"""rag-agent: offers one capability, "rag_query", which reuses the vector
index built in the RAG section (chatbot-car_rental/create_index.py) to
answer natural-language questions about the rentals dataset.

Requires chatbot-car_rental/saved_index/ to already exist - run
create_index.py from inside chatbot-car_rental/ first (section 1 of the
README) if you haven't already.

Run after issue_credentials.py has produced credentials/agent_rag.json:

    python3 agent_rag.py
"""
import os
import pickle

from langchain_ollama import ChatOllama

import config
from common.agent_server import build_agent

INDEX_PATH = os.path.join(
    config.BASE_DIR, "chatbot-car_rental", "saved_index", "vector_index_llama3_2_rentals.pkl"
)

_index = None
_llm = None


def _load_index():
    global _index, _llm
    if _index is None:
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(
                f"{INDEX_PATH} not found - run create_index.py from inside "
                "chatbot-car_rental/ first (see section 1 of the README)."
            )
        with open(INDEX_PATH, "rb") as f:
            _index = pickle.load(f)
        _llm = ChatOllama(model="llama3.2", temperature=0.7)
    return _index, _llm


def rag_query(args: dict):
    query = args.get("query", "")
    index, llm = _load_index()
    return index.query(query, llm=llm)


app, did = build_agent(
    name="rag-agent",
    skill_name="Answer questions about car rentals (RAG)",
    skill_description="Answers natural-language questions about the rentals dataset using the RAG index built in section 1.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The natural-language question to ask about the rentals dataset",
            }
        },
        "required": ["query"],
    },
    handler=rag_query,
)

if __name__ == "__main__":
    info = config.AGENTS["rag-agent"]
    print(f"rag-agent DID: {did}")
    print(f"Listening on http://{info['host']}:{info['port']}")
    app.run(host="0.0.0.0", port=info["port"])
