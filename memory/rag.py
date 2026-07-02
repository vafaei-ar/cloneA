"""Long-term memory using ChromaDB + sentence-transformers."""
import uuid
import config

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb
        from chromadb.utils import embedding_functions
        _client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        _collection = _client.get_or_create_collection(
            name=config.MEMORY_COLLECTION,
            embedding_function=ef,
        )
    return _collection


def store(text: str, metadata: dict | None = None) -> None:
    col = _get_collection()
    col.add(
        documents=[text],
        metadatas=[metadata or {}],
        ids=[str(uuid.uuid4())],
    )


def retrieve(query: str, n_results: int = 5) -> list[str]:
    col = _get_collection()
    if col.count() == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(n_results, col.count()))
    return results["documents"][0]


def build_memory_context(query: str) -> str:
    docs = retrieve(query)
    if not docs:
        return ""
    joined = "\n---\n".join(docs)
    return f"[Relevant memory]\n{joined}\n[End memory]\n\n"
