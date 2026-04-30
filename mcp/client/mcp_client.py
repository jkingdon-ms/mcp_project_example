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
from types import TracebackType

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AzureOpenAI
from openai.types.chat import ChatCompletionMessageToolCall
from typing import cast

from shared import QuestionResult, ToolCall

load_dotenv()
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

SERVER_SCRIPT = str(
    Path(__file__).resolve().parents[1] / "server" / "server.py")
PYTHON = sys.executable

SYSTEM_PROMPT = (
    "You are a helpful assistant for a pet store. "
    "Use the available tools to look up information about pets, orders, and users. "
    "Always use tools to fetch current data rather than making assumptions."
)


class MCPClient:
    """
    Async context manager that manages an MCP server subprocess and an
    Azure OpenAI client, exposing a single `process_question` method.

    Usage:
        async with MCPClient() as client:
            answer = await client.process_question("List available pets")
    """

    def __init__(
        self,
        server_script: str = SERVER_SCRIPT,
        endpoint: str | None = AZURE_OPENAI_ENDPOINT,
        model: str = AZURE_OPENAI_MODEL,
        system_prompt: str = SYSTEM_PROMPT,
        stateless: bool = False,
    ) -> None:
        self._server_script = server_script
        self._model = model
        self._system_prompt = system_prompt
        self._stateless = stateless
        self._messages: list = [
            {"role": "system", "content": system_prompt}
        ]

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is not set")
        self._openai = AzureOpenAI(
            azure_endpoint=endpoint,
            api_version="2024-04-01-preview",
            azure_ad_token_provider=token_provider,
        )

        self._stdio_ctx = None
        self._session_ctx = None
        self._session: ClientSession | None = None
        self._available_tools: list = []

    async def __aenter__(self) -> "MCPClient":
        server_params = StdioServerParameters(
            command=PYTHON,
            args=[self._server_script],
            env=None,
        )
        self._stdio_ctx = stdio_client(server_params)
        read, write = await self._stdio_ctx.__aenter__()

        self._session_ctx = ClientSession(read, write)
        self._session = await self._session_ctx.__aenter__()
        await self._session.initialize()

        tools_result = await self._session.list_tools()
        self._available_tools = [
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
        logger.info("Connected to MCP server with %d tools",
                    len(self._available_tools))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session_ctx:
            await self._session_ctx.__aexit__(exc_type, exc_val, exc_tb)
        if self._stdio_ctx:
            await self._stdio_ctx.__aexit__(exc_type, exc_val, exc_tb)

    async def process_question(self, question: str, include_toolcalls: bool = False) -> QuestionResult:
        """
        Send a question through the Azure OpenAI + MCP tool-calling loop
        and return a QuestionResult with the final answer.

        The `tool_calls` field is populated only when `include_toolcalls=True`.
        When `stateless=True`, each call uses a fresh message list and the
        shared history is never updated.
        """
        if self._stateless:
            messages: list = [
                {"role": "system", "content": self._system_prompt}]
        else:
            messages = self._messages

        messages.append({"role": "user", "content": question})
        tool_calls_made: list[ToolCall] = []

        assert self._session is not None

        # Agentic loop: call model, execute tools, repeat until no tools requested or limit reached
        MAX_ITERATIONS = 5
        answer = ""
        for _ in range(MAX_ITERATIONS):
            response = self._openai.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=self._available_tools,
            )
            response_message = response.choices[0].message
            messages.append(response_message)

            if not response_message.tool_calls:
                answer = response_message.content or ""
                break

            for tool_call in response_message.tool_calls:
                tc = cast(ChatCompletionMessageToolCall, tool_call)
                function_args = json.loads(tc.function.arguments)
                logger.info("Calling tool: %s(%s)",
                            tc.function.name, function_args)
                tool_result = await self._session.call_tool(tc.function.name, function_args)
                tool_calls_made.append(
                    ToolCall(
                        tool_name=tc.function.name,
                        tool_arguments=function_args,
                        tool_response=tool_result.structuredContent or {}
                    )
                )
                messages.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "name": tc.function.name,
                    "content": tool_result.content,
                })

        return QuestionResult(nl_answer=answer, tool_calls=tool_calls_made if include_toolcalls else [])


async def run() -> None:
    async with MCPClient() as client:
        print(f"Petstore assistant ready ({len(client._available_tools)} tools). "
              "Type your question (Ctrl+C to exit).")
        while True:
            try:
                user_input = input("\nPrompt: ").strip()
                if not user_input:
                    continue
                answer = await client.process_question(user_input)
                print(f"\nAssistant: {answer.nl_answer}")
            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except Exception as e:
                logger.error("Error in conversation loop: %s", e)
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(run())
