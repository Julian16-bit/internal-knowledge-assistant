# Internal Knowledge Assistant

A permission-aware RAG system that provides secure, grounded answers to questions about internal documents.

## Approach

This system enforces **role-based access control** at the retrieval layer, ensuring users only see documents they have permission to access.

### 1. Document Ingestion & Access Control

**Technology:** Docling (PDF extraction) + Weaviate (vector database)

- Docling extracts text while preserving table formatting, which is important for structured data like pricing tables (images are not extracted)
- Documents are relatively small (longest is around 1300 characters), so keeping them whole preserves complete context
- Each document in Weaviate stores an `access` array (e.g., `["marketing", "sales"]`) from `manifest.json`
  - Access control happens at query time with Weaviate filters, not in the LLM prompt

### 2. Permission-Scoped Retrieval (MCP Server)

**Technology:** FastMCP + Weaviate hybrid search

- Created `search_knowledge` tool that enforces permissions before retrieval
  - Takes user token -> validates -> retrieves only documents where `user.roles` overlaps with `document.access` (Uses Weaviate's `contains_any` filter)
- Combines vector similarity (semantic) + BM25 (keyword) for balanced retrieval

### 3. Grounded Answer Generation

**Technology:** OpenAI GPT-5-mini

- Explicitly treats document content as data, not instructions to prevent prompt injection
- Does not answer questions without supporting evidence
- Handles conflicting sources by preferring current documents
- Model must cite which documents it used for each claim

### 4. User Interface

**Technology:** Streamlit

- Simple chat interface with user role switching
- Shows source documents with metadata for transparency
- Chat history clears when switching users (prevents cross-contamination)

---

## Key Assumptions

1. Users are authenticated with static tokens (`users.json`) that map to roles. Each document has an `access` array in `manifest.json` listing allowed roles. Access is granted if any user role matches any document role. In production, tokens would be replaced with signed JWTs.

2. Documents with "executive committee only" are split at that line: content before the marker keeps its original access level, content after becomes `exec`-only. Other documents are stored whole.

3. Documents are short enough (<1500 characters) to store whole, preserving complete context. Longer documents would require semantic chunking while maintaining access metadata on each chunk.

4. When sources disagree (e.g., pricing in two documents), the agent is instructed to prefer the most current document and note the conflict in its response.

---

## Future Improvements

### Testing & Evaluation
- Create a golden dataset of questions with expected source documents and answers to establish a repeatable evaluation benchmark.
- Integrate the RAGAS framework to measure retrieval quality (context precision/recall) and answer faithfulness against the golden dataset.
- Experiment with retrieval parameters, chunking strategies, embedding models, prompts, and LLMs to identify the best-performing configuration through A/B testing.

### Security & Auth
- Replace static authentication tokens with signed JWTs containing user claims (e.g., user ID, roles, and expiration) that are validated on every request.
- Implement structured audit logging to record users, queries, retrieved documents, response times, and timestamps for debugging and compliance.
- Add monitoring and tracing to capture latency, error rates, token usage, cost per query, and the documents retrieved for each response.

### Agent Improvements
- Improve retrieval quality by adding a cross-encoder reranker to refine the top retrieved documents before passing them to the LLM.
- Maintain conversation history so the agent can answer follow-up questions with conversational context.
- Add clarification logic to prompt users for additional details when a query is ambiguous before performing retrieval.

### Document Processing
- Implement semantic chunking to improve retrieval while preserving document metadata and access permissions for each chunk.
- Use vision-language models to extract text and structured information from charts, diagrams, and scanned PDF content.
- Support incremental indexing by detecting modified documents and updating only the affected embeddings instead of rebuilding the entire index.

### Scalability & Operations
- Migrate from a local Weaviate instance to a managed cloud deployment with multi-tenancy to support larger workloads and multiple users.
- Deploy the MCP server over HTTP instead of stdio so it can run as a shared service rather than spawning a new subprocess for each request.
---