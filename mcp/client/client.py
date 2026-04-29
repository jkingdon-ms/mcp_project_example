"""
MCP Client — connects to the Petstore MCP server over stdio and uses
Azure OpenAI to drive a conversational loop with tool calling.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AzureOpenAI

load_dotenv()
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

SERVER_SCRIPT = str(
    Path(__file__).resolve().parents[1] / "server" / "server.py")
PYTHON = sys.executable


async def run():
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version="2024-04-01-preview",
        azure_ad_token_provider=token_provider,
    )

    # Start the MCP server as a subprocess over stdio
    server_params = StdioServerParameters(
        command=PYTHON,
        args=[SERVER_SCRIPT],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                print(f"  - {tool.name}")

            # Format tools for Azure OpenAI function calling
            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in tools_result.tools
            ]

            # Conversational loop
            messages = []
            print("\nPetstore assistant ready. Type your question (Ctrl+C to exit).")
            while True:
                try:
                    user_input = input("\nPrompt: ").strip()
                    if not user_input:
                        continue
                    messages.append({"role": "user", "content": user_input})

                    # First call — may trigger tool use
                    response = openai_client.chat.completions.create(
                        model=AZURE_OPENAI_MODEL,
                        messages=messages,
                        tools=available_tools,
                    )
                    response_message = response.choices[0].message
                    messages.append(response_message)

                    # Handle tool calls
                    if response_message.tool_calls:
                        for tool_call in response_message.tool_calls:
                            function_args = json.loads(
                                tool_call.function.arguments)
                            print(
                                f"  [calling tool: {tool_call.function.name}({function_args})]")
                            result = await session.call_tool(tool_call.function.name, function_args)
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": tool_call.function.name,
                                "content": json.dumps([c.text if hasattr(c, "text") else str(c) for c in result.content]),
                            })
                    else:
                        logger.info("No tool calls made by the model")

                    # Final response after tool results
                    final_response = openai_client.chat.completions.create(
                        model=AZURE_OPENAI_MODEL,
                        messages=messages,
                        tools=available_tools,
                    )
                    answer = final_response.choices[0].message.content
                    messages.append({"role": "assistant", "content": answer})
                    print(f"\nAssistant: {answer}")

                except KeyboardInterrupt:
                    print("\nExiting.")
                    break
                except Exception as e:
                    logger.error(f"Error in conversation loop: {e}")
                    print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(run())
