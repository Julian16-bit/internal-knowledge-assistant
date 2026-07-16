from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path
import json

# Handle both direct execution and module import
try:
    from .prompts import SYSTEM_PROMPT, create_user_message
except ImportError:
    from prompts import SYSTEM_PROMPT, create_user_message


def generate_response(openai_client: OpenAI, user_message: str, model="gpt-5-mini"):
    """Generate response using OpenAI Responses API with instructions."""
    response = openai_client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user_message
    )
    return response.output_text


async def search_and_answer(openai_client: OpenAI, user_token: str, query: str, limit=3):
    """
    Search knowledge base with MCP and generate answer.

    Args:
        openai_client: OpenAI client instance
        user_token: User authentication token
        query: User's question
        limit: Number of documents to retrieve

    Returns:
        dict with answer, documents, user info, or error
    """
    mcp_server_path = Path(__file__).parent / "mcp_server.py"

    server_params = StdioServerParameters(
        command="python",
        args=[str(mcp_server_path)]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call search_knowledge tool via MCP
            result = await session.call_tool("search_knowledge", {
                "query": query,
                "user_token": user_token,
                "limit": limit
            })

            search_data = json.loads(result.content[0].text)

            if "error" in search_data:
                return {"error": search_data["error"]}

            # Create user message with documents and query
            user_message = create_user_message(query, search_data["documents"])

            # Generate response
            answer = generate_response(openai_client, user_message)

            return {
                "answer": answer,
                "documents": search_data["documents"],
                "user": search_data["user"],
                "roles": search_data["roles"]
            }
