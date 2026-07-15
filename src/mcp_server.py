from mcp.server.fastmcp import FastMCP
import weaviate
from weaviate.classes.query import Filter
import json

# Initialize FastMCP server
mcp = FastMCP("knowledge-assistant")

# Load users data
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
USERS_FILE = BASE_DIR / "data" / "users.json"

with open(USERS_FILE, "r", encoding="utf-8") as f:
    USERS_DATA = json.load(f)


def get_user_from_token(token):
    """Resolve token to user with roles."""
    for user in USERS_DATA["users"]:
        if user["token"] == token:
            return user
    return None


@mcp.tool()
def search_knowledge(query: str, user_token: str, limit: int = 3) -> str:
    """
    Search internal knowledge base with role-based access control.

    Args:
        query: The search query
        user_token: User's authentication token
        limit: Maximum number of documents to return

    Returns:
        JSON string with accessible documents
    """
    # Authenticate user
    user = get_user_from_token(user_token)
    if not user:
        return json.dumps({"error": "Invalid token"})

    # Connect to Weaviate
    client = weaviate.connect_to_local(host="localhost", port=8080)

    try:
        documents_collection = client.collections.get("Document")

        # Hybrid search with role-based filtering
        search_results = documents_collection.query.hybrid(
            query=query,
            alpha=0.6,
            filters=Filter.by_property("access").contains_any(user["roles"]),
            limit=limit
        )

        # Format results
        results = []
        for obj in search_results.objects:
            results.append({
                "title": obj.properties["title"],
                "content": obj.properties["content"],
                "source": obj.properties["source"],
                "period": obj.properties["period"],
                "status": obj.properties["status"]
            })

        return json.dumps({
            "user": user["name"],
            "roles": user["roles"],
            "documents": results
        }, indent=2)

    finally:
        client.close()


if __name__ == "__main__":
    mcp.run()
