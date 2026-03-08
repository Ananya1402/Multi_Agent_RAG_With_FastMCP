"""RAG Agent – retrieves answers from the FAQ vector database."""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings
from app.rag.vectorstore import similarity_search

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are a helpful FAQ assistant. Answer the user's question
based ONLY on the provided context from the FAQ database. If the context does not
contain enough information to answer the question, respond with:
"I'm sorry, I couldn't find an answer to that question in our FAQ database."

Do NOT make up answers. Only use information from the retrieved context.

Context:
{context}
"""


def _format_context(docs) -> str:
    """Format retrieved documents into a context string."""
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(f"[{i}] {doc.page_content}")
    return "\n\n".join(parts)


async def handle_rag_query(query: str) -> str:
    """Process an FAQ query through the RAG pipeline.

    1. Perform semantic search on the vector store
    2. Build a context from retrieved documents
    3. Generate an answer using the LLM, grounded in the context

    Args:
        query: The user's FAQ question.

    Returns:
        The generated answer string.
    """
    logger.info("RAG Agent processing query: %s", query[:100])

    # Step 1: Retrieve relevant documents
    docs = similarity_search(query, k=4)

    if not docs:
        return "I'm sorry, I couldn't find an answer to that question in our FAQ database."

    # Step 2: Build context
    context = _format_context(docs)
    logger.info("Retrieved %d documents for context", len(docs))

    # Step 3: Generate answer with LLM
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.1,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )

    chain = prompt | llm
    response = await chain.ainvoke({"context": context, "question": query})
    return response.content
