"""rental-agent: offers one capability, "list_rentals", read straight from
the same dataset/rentals.csv used in the RAG section. This is the
successor to the old MCP tool that used to call the Tomcat servlet.

Run after issue_credentials.py has produced credentials/agent_rental.json:

    python3 agent_rental.py
"""
import csv
import os

import config
from common.agent_server import build_agent

RENTALS_CSV = os.path.join(config.BASE_DIR, "chatbot-car_rental", "dataset", "rentals.csv")


def list_rentals(args: dict):
    with open(RENTALS_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    return [", ".join(f"{k}={v}" for k, v in row.items()) for row in rows]


app, did = build_agent(
    name="rental-agent",
    skill_name="List car rentals",
    skill_description="Returns the current list of car rentals from the local dataset.",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=list_rentals,
)

if __name__ == "__main__":
    info = config.AGENTS["rental-agent"]
    print(f"rental-agent DID: {did}")
    print(f"Listening on http://{info['host']}:{info['port']}")
    app.run(host="0.0.0.0", port=info["port"])
