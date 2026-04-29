from pathlib import Path

import httpx
import yaml
from fastmcp import FastMCP

BASE_URL = "http://localhost:8080/v2"
SPEC_PATH = Path(__file__).resolve(
).parents[2] / "api" / "server" / "openapi_server" / "openapi" / "openapi.yaml"

# Create an HTTP client pointed at the local API server
client = httpx.AsyncClient(base_url=BASE_URL)

# Load the OpenAPI 3.0 spec from the generated server file
with open(SPEC_PATH) as f:
    openapi_spec = yaml.safe_load(f)

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Petstore API"
)

if __name__ == "__main__":
    mcp.run()
