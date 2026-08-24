import hashlib
import logging
import os
import re
from typing import List

from resume_parser.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Direct working embedding model
EMBEDDING_MODEL = "gemini-embedding-001"


def _get_client():
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "").strip().strip("'").strip('"')
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _fallback_deterministic_embedding(text: str, dim: int = 768) -> List[float]:
    tokens = re.findall(r"\w+", text.lower())
    vec = [0.0] * dim
    if not tokens:
        return vec

    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0

    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def embed_text(text: str) -> List[float]:
    if not text or not text.strip():
        raise ValueError("Cannot create an embedding from empty text.")

    client = _get_client()

    if client is not None:
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
            )
            embeddings = getattr(response, "embeddings", None) or []
            if embeddings:
                values = getattr(embeddings[0], "values", None)
                if values:
                    return list(values)
        except Exception as exc:
            logger.warning("Gemini remote embedding failed: %s. Using local fallback.", exc)

    return _fallback_deterministic_embedding(text)