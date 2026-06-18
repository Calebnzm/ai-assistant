from functools import lru_cache
from typing import Iterable, List
import os

from openai import OpenAI

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "384"))


@lru_cache(maxsize=1)
def _openai_client() -> OpenAI:
    return OpenAI()


def _normalize_text(text: str) -> str:
    return (text or "").replace("\n", " ").strip()


def embed_text(text: str) -> List[float]:
    response = _openai_client().embeddings.create(
        model=EMBEDDING_MODEL,
        input=[_normalize_text(text)],
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return response.data[0].embedding


def embed_texts(texts: Iterable[str]) -> List[List[float]]:
    normalized = [_normalize_text(text) for text in texts]
    response = _openai_client().embeddings.create(
        model=EMBEDDING_MODEL,
        input=normalized,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in response.data]
