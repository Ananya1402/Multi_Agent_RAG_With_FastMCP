"""CSV FAQ data loader – reads question/answer pairs into LangChain Documents."""

import csv
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from app.config import settings


def load_faq_documents(csv_path: str | None = None) -> List[Document]:
    """Load FAQ data from a CSV file and return a list of LangChain Documents.

    Each row becomes a Document with:
      - page_content = "Question: {q}\nAnswer: {a}"
      - metadata = {"source": "faq", "question": q, "row": index}
    """
    path = Path(csv_path or settings.FAQ_CSV_PATH)
    if not path.is_absolute():
        # Resolve relative to the backend directory
        path = Path(__file__).resolve().parent.parent.parent / path

    if not path.exists():
        raise FileNotFoundError(f"FAQ CSV not found at {path}")

    documents: List[Document] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            question = row.get("question", "").strip()
            answer = row.get("answer", "").strip()
            if not question or not answer:
                continue
            content = f"Question: {question}\nAnswer: {answer}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": "faq",
                        "question": question,
                        "row": idx,
                    },
                )
            )
    return documents
