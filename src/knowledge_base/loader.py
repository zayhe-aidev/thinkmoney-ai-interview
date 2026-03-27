"""Knowledge base loader using ChromaDB for semantic search over markdown files."""

import hashlib
import re
from pathlib import Path

import chromadb


DATA_DIR = Path(__file__).parent / "data"
CHROMA_DIR = Path(__file__).parent.parent.parent / ".chroma"


class KnowledgeBase:
    """Semantic search over thinkmoney knowledge base markdown files.

    Uses ChromaDB with its built-in default embedding model (runs locally,
    no API calls needed). The vector store is persisted to disk so
    subsequent runs skip the embedding step.
    """

    def __init__(self, data_dir: Path | None = None, persist_dir: Path | None = None):
        self._data_dir = data_dir or DATA_DIR
        self._persist_dir = persist_dir or CHROMA_DIR
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._collection = self._client.get_or_create_collection(
            name="thinkmoney_kb",
            metadata={"hnsw:space": "cosine"},
        )
        self._ensure_indexed()

    def _ensure_indexed(self):
        """Index markdown files if the collection is empty or content has changed."""
        sections = self._load_sections()
        if not sections:
            return

        # Check if we need to re-index by comparing a content hash
        content_hash = hashlib.md5(
            "".join(s["text"] for s in sections).encode()
        ).hexdigest()

        existing = self._collection.get(ids=["__meta__"])
        if existing["ids"] and existing["metadatas"]:
            stored_hash = existing["metadatas"][0].get("content_hash", "")
            if stored_hash == content_hash:
                return  # Already indexed, skip

        # Clear and re-index
        # Delete all existing documents
        all_ids = self._collection.get()["ids"]
        if all_ids:
            self._collection.delete(ids=all_ids)

        # Add sections
        ids = []
        documents = []
        metadatas = []

        for i, section in enumerate(sections):
            ids.append(f"section_{i}")
            documents.append(section["text"])
            metadatas.append({
                "source": section["source"],
                "heading": section["heading"],
            })

        self._collection.add(ids=ids, documents=documents, metadatas=metadatas)

        # Store content hash for cache invalidation
        self._collection.add(
            ids=["__meta__"],
            documents=["metadata"],
            metadatas=[{"content_hash": content_hash}],
        )

    def _load_sections(self) -> list[dict]:
        """Split markdown files into sections by ## headings."""
        sections = []

        for md_file in sorted(self._data_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            source = md_file.stem

            # Split by ## headings
            parts = re.split(r"(?=^## )", content, flags=re.MULTILINE)

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # Extract heading
                heading_match = re.match(r"^##\s+(.+)", part)
                heading = heading_match.group(1) if heading_match else source

                # Skip the top-level # heading section if it has no real content
                if part.startswith("# ") and "##" not in part:
                    lines = part.split("\n", 1)
                    if len(lines) < 2 or not lines[1].strip():
                        continue

                sections.append({
                    "text": part,
                    "source": source,
                    "heading": heading,
                })

        return sections

    def search(self, query: str, n_results: int = 3) -> str:
        """Search the knowledge base for sections relevant to the query.

        Args:
            query: Natural language search query.
            n_results: Maximum number of sections to return.

        Returns:
            Formatted string with matching sections and their sources.
        """
        # Don't count the __meta__ doc
        total = self._collection.count()
        if total <= 1:
            return "No knowledge base content found."

        results = self._collection.query(
            query_texts=[query],
            n_results=min(n_results, total - 1),
            where={"source": {"$ne": ""}},  # Exclude __meta__
        )

        if not results["documents"] or not results["documents"][0]:
            return "No relevant information found."

        output_parts = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            source = meta.get("source", "unknown")
            output_parts.append(f"[Source: {source}]\n{doc}")

        return "\n\n---\n\n".join(output_parts)
