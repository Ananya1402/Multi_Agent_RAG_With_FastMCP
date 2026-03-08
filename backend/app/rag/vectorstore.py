"""ChromaDB vector store – builds and queries the FAQ vector database."""

import logging
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.config import settings
from app.rag.loader import load_faq_documents

logger = logging.getLogger(__name__)

# Module-level singleton
_vectorstore: Optional[Chroma] = None


def get_embeddings() -> OpenAIEmbeddings:
    """Return the OpenAI embeddings model."""
    return OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY,
        model="text-embedding-3-small",
    )


def build_vectorstore(force_rebuild: bool = False) -> Chroma:
    """Build (or load) the ChromaDB vector store from FAQ CSV data."""
    global _vectorstore

    if _vectorstore is not None and not force_rebuild:
        return _vectorstore

    embeddings = get_embeddings()

    # Try loading existing persisted store
    if not force_rebuild:
        try:
            store = Chroma(
                collection_name=settings.CHROMA_COLLECTION_NAME,
                embedding_function=embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIR,
            )
            # Check if it has data
            if store._collection.count() > 0:
                logger.info(
                    "Loaded existing ChromaDB with %d documents",
                    store._collection.count(),
                )
                _vectorstore = store
                return _vectorstore
        except Exception:
            logger.info("No existing ChromaDB found, building new one.")

    # Load FAQ documents and create vector store
    documents = load_faq_documents()
    logger.info("Loaded %d FAQ documents, building vector store...", len(documents))

    _vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )
    logger.info(
        "ChromaDB built with %d documents", _vectorstore._collection.count()
    )
    return _vectorstore


def get_vectorstore() -> Chroma:
    """Return the initialised vector store (builds if needed)."""
    return build_vectorstore()


def similarity_search(query: str, k: int = 4) -> List[Document]:
    """Perform semantic similarity search against the FAQ vector store."""
    store = get_vectorstore()
    return store.similarity_search(query, k=k)


def similarity_search_with_score(
    query: str, k: int = 4
) -> List[tuple[Document, float]]:
    """Search with relevance scores (lower = more similar for cosine)."""
    store = get_vectorstore()
    return store.similarity_search_with_score(query, k=k)
