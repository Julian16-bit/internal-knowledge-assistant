from openai import OpenAI
from dotenv import load_dotenv
import os
import asyncio
from agent_utils import search_and_answer


async def main():
    """Main RAG pipeline with MCP tool integration."""
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # Get user input
    user_token = input("Enter your token: ")
    user_query = input("Type a question: ")

    # Search and generate answer
    result = await search_and_answer(openai_client, user_token, user_query)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    # Display result
    print("ANSWER:")
    print(result["answer"])

    print("\n\n")
    print(f"SOURCES ({len(result['documents'])} documents):")
    for doc in result["documents"]:
        print(f"- {doc['title']} ({doc['status']}, {doc['period']})")


if __name__ == "__main__":
    asyncio.run(main())

