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

1. Users are authenticated with static tokens (`users.json`) that map to roles. Each document has an `access` array in `manifest.json` listing allowed roles. Access is granted if any user role matches any document role. In production, tokens would be replaced with signed JWTs, but the MCP tool boundary makes this swap straightforward.

2. Documents containing "executive committee only" (case-insensitive) are split at the line boundary where the marker appears. Text before the marker retains the document's original access level; the marker line and everything after becomes `exec`-only. Documents without the marker or already marked `exec` are stored whole.

3. Documents are short enough (<2000 tokens) to store whole, preserving complete context. Longer documents would require semantic chunking while maintaining access metadata on each chunk.

4. When sources disagree (e.g., pricing in two documents), the agent is instructed to prefer the most current document and note the conflict in its response.

---

## Next Steps

### Security & Auth
- Replace static tokens with signed JWTs with expiry and scopes
- Add audit logging for all document access (who queried what, when)
- Implement rate limiting per user/role


---