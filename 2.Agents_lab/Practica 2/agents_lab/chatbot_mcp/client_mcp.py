import asyncio
from contextlib import AsyncExitStack
from pathlib import Path
import sys

import logging

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Ollama imports
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

load_dotenv()

# Ollama model
OLLAMA_MODEL = "llama3.2"  # or "llama3.2:3b", "llama3.1", etc.
#OLLAMA_MODEL = "llama3.2:1b"  # or "llama3.2:3b", "llama3.1", etc.

class MCPClient:
    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        # Initialize Ollama LLM with tool calling support
        # NOTE: do NOT set format="json" here - Ollama's own tool-calling
        # protocol (used by bind_tools) already handles structured tool-call
        # args; format="json" instead forces every model turn, including the
        # final natural-language summary after the tool result comes back,
        # to be raw JSON. With no schema for that turn the model either
        # emits an empty "{}" or never produces a stopping (non-tool-call)
        # response at all, causing list_rentals to be called on a loop.
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            temperature=0.7,
        ).bind_tools([])  # we'll bind tools dynamically

    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        if is_python:
            path = Path(server_script_path).resolve()
            server_params = StdioServerParameters(
                command="python3",           # ← using python3 directly
                args=[str(path)],
                env=None,
            )
        else:
            server_params = StdioServerParameters(command="node", args=[server_script_path], env=None)

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

        # Bind the actual tools to the LLM for proper tool calling
        tool_defs = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools
        ]
        #for tool in tools:
        #    print(tool)
        
        self.llm_with_tools = self.llm.bind_tools(tool_defs)

    async def process_query(self, query: str) -> str:
        messages = [HumanMessage(content=query)] # 1. Start with user query

        final_text = []

        while True: # Main tool-calling loop
        
            # Invoke the LLM with current messages
            # 2. Send current message history to Ollama

            response = self.llm_with_tools.invoke(messages)

            # Append assistant's text response (if any)
            # 3. If Ollama produced text, record it
            if response.content:
                final_text.append(response.content)

            # Check if there are tool calls
            # 4. Check if Ollama wants to call any tools
            if not response.tool_calls:
                break  # No more tool calls, done

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # 5. Log that we're calling the tool
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                
                # 6. Execute the tool on the MCP server
                # Execute the tool via MCP session
                result = await self.session.call_tool(tool_name, tool_args)
                
                # 7. Add messages to history so Ollama sees what happened:
            	#    - The assistant's message containing the tool call
            	#    - The tool's result as a ToolMessage
                # Add tool result back to conversation
                messages.append(response)  # Assistant message with tool call
                messages.append(ToolMessage(
                    content=result.content,
                    tool_call_id=tool_call["id"],
                ))

        return "\n".join(final_text)

    async def chat_loop(self):
        print("\nMCP Client Started! (Powered by local Ollama - llama3.2)")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")
                import traceback
                traceback.print_exc()

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
