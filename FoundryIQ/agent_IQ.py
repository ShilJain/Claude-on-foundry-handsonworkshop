import asyncio
import os

from dotenv import load_dotenv
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import AnthropicFoundryClient

# 1. Load environment variables from .env
load_dotenv()

CUPCAKE_MCP_URL = os.getenv(
    "CUPCAKE_MCP_URL",
    "https://ca-cupcake-mcp.jollyrock-23017c57.westus2.azurecontainerapps.io/mcp/",
)
KNOWLEDGE_BASE_NAME = os.getenv("KNOWLEDGE_BASE_NAME", "cupcake-store-kb")


async def main() -> None:
    # 2. Configure the chat model (Claude on Microsoft Foundry)
    chat_client = AnthropicFoundryClient(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )

    # 3. Connect to the Cupcake Store MCP server (ordering, stock, orders)
    cupcake_tool = MCPStreamableHTTPTool(
        name="cupcake-store",
        url=CUPCAKE_MCP_URL,
    )
    # 4. Configure the Foundry IQ knowledge base MCP endpoint
    #    (store policies: hours, delivery, returns). The api-key header
    #    authenticates against Azure AI Search.
    search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
    search_key = os.environ["AZURE_SEARCH_API_KEY"]
    kb_url = f"{search_endpoint}/knowledgebases/{KNOWLEDGE_BASE_NAME}/mcp?api-version=2026-05-01-preview"
    knowledge_base_tool = MCPStreamableHTTPTool(
        name="cupcake-knowledge-base",
        url=kb_url,
        header_provider=lambda _: {"api-key": search_key},
        load_prompts=False,
    )
    # 5. Create the agent with both MCP tools
    instructions = (
        "You are Sparkles, the Cupcake Store assistant. Use the cupcake-store "
        "tool for ordering, inventory, and order status. Use the "
        "cupcake-knowledge-base tool for store policies such as hours, delivery, "
        "shipping, and returns. Do not invent store information; use the "
        "appropriate tool when an answer depends on store data."
    )

    agent = Agent(
        client=chat_client,
        name="cupcake-agent",
        instructions=instructions,
        tools=[cupcake_tool, knowledge_base_tool],
    )

    # 6. Start a chat session and talk to the agent
    session = agent.create_session()
    print("Sparkles is ready. Type 'exit' to quit.\n")

    response = await agent.run("hello", session=session)
    print(f"\033[1;35mAssistant:\033[0m\n{response.text}\n")

    while True:
        user_input = input("\033[1;35mYou:\033[0m\n")
        if user_input.lower() in ("exit", "quit"):
            break

        response = await agent.run(user_input, session=session)
        print(f"\n\033[1;35mAssistant:\033[0m\n{response.text}\n")


if __name__ == "__main__":
    asyncio.run(main())