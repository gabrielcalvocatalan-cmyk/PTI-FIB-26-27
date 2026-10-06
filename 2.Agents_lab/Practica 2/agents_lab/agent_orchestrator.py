"""The orchestrator: the "front door" a user talks to. It discovers the
other agents' capabilities from their agent cards (like client_mcp.py did
for MCP tools), but - unlike the MCP version - it does not just trust
whichever agent claims a capability. Before calling a peer it fetches that
peer's Verifiable Credential and checks it was issued by the trust anchor
this orchestrator is configured to trust, for the DID that agent actually
claims, listing the capability being requested.

Run after trust_anchor.py, issue_credentials.py, agent_rental.py and
agent_rag.py are all up:

    python3 agent_orchestrator.py
"""
import requests
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage

import config
from common.identity import load_or_create_identity, verify_capability_credential

OLLAMA_MODEL = "llama3.2"


class Orchestrator:
    def __init__(self):
        # The orchestrator has its own DID too, though nothing in the base
        # flow needs to resolve it - see the README's self-proposed
        # extension ideas for what having it enables (mutual auth).
        self.did, _ = load_or_create_identity(
            "orchestrator", config.HOST, config.ORCHESTRATOR_PORT, config.KEYS_DIR
        )
        self.trust_anchor_did = config.trust_anchor_did()

        self.cards = {}          # agent_name -> agent-card.json
        self.skill_to_agent = {} # skill/capability id -> agent_name

        # Unlike client_mcp.py, we don't force format="json": our /invoke
        # results are plain strings, not JSON, and forcing JSON output
        # measurably hurts the final natural-language answer quality with
        # small local models (verified: with format="json" the model tends
        # to just emit "{}" instead of summarizing the tool result).
        self.llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.7)
        self.llm_with_tools = None

    def discover(self):
        """Fetch every agent's card and turn its declared skill into an
        Ollama tool definition - the same bind_tools pattern client_mcp.py
        uses for MCP tools, just sourced from HTTP agent cards instead."""
        tool_defs = []

        for agent_name, info in config.AGENTS.items():
            base_url = config.agent_base_url(info)
            card = requests.get(f"{base_url}/.well-known/agent-card.json", timeout=5).json()
            self.cards[agent_name] = card

            skill = card["skills"][0]
            self.skill_to_agent[skill["id"]] = agent_name
            tool_defs.append({
                "type": "function",
                "function": {
                    "name": skill["id"],
                    "description": skill["description"],
                    "parameters": skill["parameters"],
                },
            })
            print(f"Discovered {agent_name}: skill={skill['id']!r} did={card['securitySchemes']['didAuth']['did']}")

        self.llm_with_tools = self.llm.bind_tools(tool_defs)

    def call_agent(self, capability: str, args: dict) -> str:
        agent_name = self.skill_to_agent.get(capability)
        if agent_name is None:
            return f"[error] no known agent offers capability {capability!r}"

        info = config.AGENTS[agent_name]
        base_url = config.agent_base_url(info)
        card = self.cards[agent_name]
        claimed_did = card["securitySchemes"]["didAuth"]["did"]

        print(f"\n[trust check] verifying {agent_name} ({claimed_did}) before calling {capability!r}...")
        vc = requests.get(f"{base_url}/credential.json", timeout=5).json()
        ok, reason = verify_capability_credential(
            vc,
            expected_subject_did=claimed_did,
            required_capability=capability,
            trusted_issuer_did=self.trust_anchor_did,
        )

        if not ok:
            print(f"[trust check] FAILED: {reason}")
            return f"[refused] trust check failed for {agent_name}: {reason}"

        print("[trust check] OK - credential valid, issued by the trust anchor, capability listed.")

        response = requests.post(
            f"{base_url}/invoke",
            json={"capability": capability, "args": args},
            timeout=180,  # was 30
        )
        response.raise_for_status()
        return str(response.json().get("result"))

    def process_query(self, query: str) -> str:
        messages = [HumanMessage(content=query)]
        final_text = []

        while True:
            response = self.llm_with_tools.invoke(messages)

            if response.content:
                final_text.append(response.content)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                capability = tool_call["name"]
                args = tool_call["args"]
                final_text.append(f"[Calling {capability} with args {args}]")

                result = self.call_agent(capability, args)

                messages.append(response)
                messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

        return "\n".join(final_text)

    def chat_loop(self):
        print("\nAgent network orchestrator started! (Powered by local Ollama - llama3.2)")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                print("\n" + self.process_query(query))
            except Exception as e:
                print(f"\nError: {e}")


def main():
    orchestrator = Orchestrator()
    print(f"Orchestrator DID: {orchestrator.did}")
    print(f"Trusted issuer (trust anchor) DID: {orchestrator.trust_anchor_did}")
    orchestrator.discover()
    orchestrator.chat_loop()


if __name__ == "__main__":
    main()
