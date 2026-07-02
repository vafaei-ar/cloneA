"""Long-term memory using ChromaDB + sentence-transformers.

Two kinds of documents live in the collection:
  * type="conversation" — tagged with the Telegram user_id it came from.
  * type="persona"      — ingested chat history that defines the clone's
                          voice/persona; shared across all users.

Retrieval returns the current user's own conversation memories *plus* the
shared persona memories, so one user's private chats never leak into another
user's context.
"""
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


def _where_for_user(user_id: str | int | None) -> dict | None:
    """Restrict a query to this user's own memories plus shared persona memories."""
    if user_id is None:
        return None
    return {"$or": [{"user_id": str(user_id)}, {"type": "persona"}]}


def retrieve(query: str, n_results: int = 5, user_id: str | int | None = None) -> list[str]:
    col = _get_collection()
    if col.count() == 0:
        return []
    results = col.query(
        query_texts=[query],
        n_results=min(n_results, col.count()),
        where=_where_for_user(user_id),
    )
    docs = results.get("documents") or [[]]
    return docs[0]


def build_memory_context(query: str, user_id: str | int | None = None) -> str:
    docs = retrieve(query, user_id=user_id)
    if not docs:
        return ""
    joined = "\n---\n".join(docs)
    return f"[Relevant memory]\n{joined}\n[End memory]\n\n"
