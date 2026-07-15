# Quickstart Guide

## Prerequisites

- Python 3.9+
- Docker Desktop (for Weaviate)
- OpenAI API key

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_api_key_here
```

### 3. Start Weaviate

```bash
docker-compose up -d
```

This starts Weaviate on `localhost:8080`.

### 4. Load Documents

```bash
cd src
python load_documents.py
```

This will:
- Convert all PDFs in `data/pdfs/` to text using Docling
- Load them into Weaviate with metadata from `data/manifest.json`
- Apply access control labels from the manifest

## Running the Agent

### Command Line Interface

```bash
cd src
python run_agent.py
```

When prompted:
- Enter a user token (e.g., `tok_marketing_demo`)
- Ask a question about the documents

### Streamlit Web Interface

```bash
cd src
streamlit run app.py
```

Then:
- Select a user from the sidebar dropdown
- Chat with the knowledge assistant

## Available Test Users

| User | Token | Roles | Access |
|------|-------|-------|--------|
| Maria (Marketing) | `tok_marketing_demo` | marketing | Marketing docs + general |
| Sam (Sales) | `tok_sales_demo` | sales, marketing | Sales + marketing docs + general |
| Priya (People/HR) | `tok_people_demo` | people | HR docs + general |
| Erin (Exec) | `tok_exec_demo` | exec, finance, marketing, sales, ops, people | All documents |
