import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import AnthropicFoundryClient
from agent_framework_foundry_hosting import ResponsesHostServer
from dotenv import load_dotenv


load_dotenv()

CUPCAKE_MCP_URL = os.getenv(
    "CUPCAKE_MCP_URL",
    "https://ca-cupcake-mcp.jollyrock-23017c57.westus2.azurecontainerapps.io/mcp/",
)
KNOWLEDGE_BASE_NAME = os.getenv("KNOWLEDGE_BASE_NAME", "cupcake-store-kb")


def require_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def create_agent() -> Agent:
    chat_client = AnthropicFoundryClient(
        model=require_setting("FOUNDRY_MODEL_DEPLOYMENT"),
        api_key=require_setting("FOUNDRY_API_KEY"),
        base_url=require_setting("FOUNDRY_ENDPOINT"),
    )

    cupcake_tool = MCPStreamableHTTPTool(
        name="cupcake-store",
        url=CUPCAKE_MCP_URL,
    )

    search_endpoint = require_setting("AZURE_SEARCH_ENDPOINT").rstrip("/")
    search_key = require_setting("AZURE_SEARCH_API_KEY")
    knowledge_base_url = (
        f"{search_endpoint}/knowledgebases/{KNOWLEDGE_BASE_NAME}/mcp"
        "?api-version=2026-05-01-preview"
    )
    knowledge_base_tool = MCPStreamableHTTPTool(
        name="cupcake-knowledge-base",
        url=knowledge_base_url,
        header_provider=lambda _: {"api-key": search_key},
        load_prompts=False,
    )

    return Agent(
        client=chat_client,
        name="cupcake-agent",
        instructions=(
            "You are Sparkles, the Cupcake Store assistant. Use the cupcake-store "
            "tool for ordering, inventory, and order status. Use the "
            "cupcake-knowledge-base tool for store policies such as hours, delivery, "
            "shipping, and returns. Do not invent store information; use the "
            "appropriate tool when an answer depends on store data."
        ),
        tools=[cupcake_tool, knowledge_base_tool],
    )


def main() -> None:
    ResponsesHostServer(create_agent()).run()


if __name__ == "__main__":
    main()