import weaviate
from weaviate.classes.config import Configure, Property, DataType
from docling.document_converter import DocumentConverter
from pathlib import Path
import json
import re

# Setup paths relative to this file
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MANIFEST_FILE = DATA_DIR / "manifest.json"
PDFS_DIR = DATA_DIR / "pdfs"

EXEC_MARKER = re.compile(r"executive committee only", re.IGNORECASE)

def split_by_access(content: str, doc_access: list[str]):
    """Split document at exec-only marker into segments with different access levels."""
    match = EXEC_MARKER.search(content)
    if not match or doc_access == ["exec"]:
        return [(content, doc_access)]

    line_start = content.rfind("\n", 0, match.start()) + 1
    public = content[:line_start].strip()
    confidential = content[line_start:].strip()

    segments = []
    if public:
        segments.append((public, doc_access))
    if confidential:
        segments.append((confidential, ["exec"]))
    return segments

# Connect to local Weaviate instance
client = weaviate.connect_to_local(host="localhost", port=8080)

try:
    # Load manifest for metadata and access control
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Create a lookup dict by document path
    manifest_lookup = {doc["path"]: doc for doc in manifest["documents"]}

    # Delete existing collection if it exists (avoid duplicates)
    if client.collections.exists("Document"):
        client.collections.delete("Document")
        print("Deleted existing Document collection")

    # Create collection for documents
    client.collections.create(
        name="Document",
        vectorizer_config=Configure.Vectorizer.text2vec_openai(),
        properties=[
            Property(name="filename", data_type=DataType.TEXT),
            Property(name="filepath", data_type=DataType.TEXT),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="access", data_type=DataType.TEXT_ARRAY),
            Property(name="period", data_type=DataType.TEXT),
            Property(name="source", data_type=DataType.TEXT),
            Property(name="status", data_type=DataType.TEXT),
            Property(name="note", data_type=DataType.TEXT),
        ]
    )

    documents_collection = client.collections.get("Document")

    # Initialize Docling converter
    converter = DocumentConverter()

    # Process all PDFs in the pdfs folder
    pdf_files = list(PDFS_DIR.rglob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files to process")

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        # Convert PDF to text using Docling
        result = converter.convert(str(pdf_path))
        content = result.document.export_to_text()

        # Get relative path for manifest lookup
        relative_path = str(pdf_path.relative_to(PDFS_DIR)).replace("\\", "/")
        metadata = manifest_lookup.get(relative_path, {})

        # Store in Weaviate - split off any exec-only paragraph first
        doc_access = metadata.get("access", [])
        for seg_content, seg_access in split_by_access(content, doc_access):
            documents_collection.data.insert(
                properties={
                    "filename": pdf_path.name,
                    "filepath": str(pdf_path),
                    "content": seg_content,
                    "title": metadata.get("title", pdf_path.name),
                    "access": seg_access,
                    "period": metadata.get("period", ""),
                    "source": metadata.get("source", ""),
                    "status": metadata.get("status", ""),
                    "note": metadata.get("note", ""),
                }
            )

        print(f"Loaded: {pdf_path.name} (access: {', '.join(doc_access)})")

    print(f"\nSuccessfully loaded {len(pdf_files)} documents into Weaviate")

finally:
    client.close()