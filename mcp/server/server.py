from pathlib import Path

import httpx
import yaml
from fastmcp import FastMCP
from fastmcp.server.openapi import OpenAPIResource, OpenAPIResourceTemplate, OpenAPITool
from fastmcp.utilities.openapi.models import HTTPRoute

from shared.api.api_server_manager import ApiServerManager
from tool_descriptions import CUSTOM_TOOL_DESCRIPTIONS, ToolDescriptions

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_BASE_URL = "http://localhost:8080/v2"
DEFAULT_SPEC_PATH = ROOT / "api" / "server" / \
    "openapi_server" / "openapi" / "openapi.yaml"


class MCPServer:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        spec_path: Path = DEFAULT_SPEC_PATH,
        start_api_server: bool = False,
        tool_descriptions: ToolDescriptions = CUSTOM_TOOL_DESCRIPTIONS,
    ) -> None:
        self._api_manager = ApiServerManager() if start_api_server else None
        self._tool_descriptions = tool_descriptions

        with open(spec_path) as f:
            openapi_spec = yaml.safe_load(f)

        http_client = httpx.AsyncClient(base_url=base_url)

        self.mcp = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=http_client,
            name="Petstore API",
            mcp_component_fn=self._customize_components,
        )

    def _customize_components(
        self,
        route: HTTPRoute,
        component: OpenAPITool | OpenAPIResource | OpenAPIResourceTemplate,
    ) -> None:
        if isinstance(component, OpenAPITool):
            custom_description = self._tool_descriptions.get(component.name)
            if custom_description:
                component.description = custom_description
            print(f"[Tool] {component.name}: {component.description}")

    def run(self) -> None:
        if self._api_manager:
            self._api_manager.start()
        try:
            self.mcp.run()
        finally:
            if self._api_manager:
                self._api_manager.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--start-api-server", action="store_true",
                        help="Start the API server before running the MCP server")
    args = parser.parse_args()

    MCPServer(start_api_server=args.start_api_server).run()
