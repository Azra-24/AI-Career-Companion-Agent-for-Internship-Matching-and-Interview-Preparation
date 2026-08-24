import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from resume_parser.config import BASE_DIR, GEMINI_API_KEY
from resume_parser.services.candidate_profile import candidate_to_embedding_text
from resume_parser.services.vector_store import InternshipVectorStore, internship_to_text

logger = logging.getLogger(__name__)

DATASET_PATH = BASE_DIR / "data" / "internships.json"
INDEX_PATH = BASE_DIR / "vector_db" / "internships.faiss"
METADATA_PATH = BASE_DIR / "vector_db" / "internships_metadata.json"

store = InternshipVectorStore(INDEX_PATH, METADATA_PATH)

# Models to attempt in sequence during high-traffic spikes
EXPLANATION_MODELS = [
    "gemini-3.6-flash",
    "gemini-2.5-flash",
    "gemini-1.5-pro",
]


def load_internships() -> List[Dict[str, Any]]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Internship dataset not found at {DATASET_PATH}")
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def build_internship_index() -> int:
    internships = load_internships()
    return store.build(internships)


def search_internships(candidate: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
    candidate_text = candidate_to_embedding_text(candidate)
    if not candidate_text or not candidate_text.strip():
        raise ValueError("Candidate profile does not contain enough information for matching.")

    if store.index is None and not store.load():
        logger.info("Vector index not found on disk. Building new index from dataset...")
        build_internship_index()

    matches = store.search(candidate_text, top_k=top_k)
    return [
        {**internship, "similarity_score": round(score, 4)}
        for internship, score in matches
    ]


def explain_matches(candidate: Dict[str, Any], matches: List[Dict[str, Any]]) -> str:
    """
    RAG layer: Explains match reasoning grounded strictly on candidate and retrieved context.
    Includes automated retries and model fallbacks for 503/429 status spikes.
    """
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "").strip().strip("'").strip('"')
    if not api_key or not matches:
        return ""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        context = "\n\n".join(
            f"INTERNSHIP {i + 1}:\n{internship_to_text(match)}\nSimilarity score: {match.get('similarity_score', 'N/A')}"
            for i, match in enumerate(matches)
        )
        candidate_text = candidate_to_embedding_text(candidate)

        prompt = f"""
You are an expert AI career advisor explaining semantic internship matches.
Use ONLY the candidate profile and retrieved internship records below.
Do not invent requirements, skills, companies, locations, scores, or experience.
For each internship:
1. Explain the strongest evidence for the match.
2. Note any requirements or preferred qualifications from the internship not explicitly present in the candidate profile.

CANDIDATE:
{candidate_text}

RETRIEVED INTERNSHIPS:
{context}
""".strip()

        last_error = None
        for model_name in EXPLANATION_MODELS:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.2),
                    )
                    text = (getattr(response, "text", "") or "").strip()
                    if text:
                        return text
                except Exception as err:
                    last_error = err
                    logger.warning("Attempt %d with %s failed: %s", attempt + 1, model_name, err)
                    time.sleep(1.0)  # Brief pause before retrying or switching models

        return f"RAG explanation unavailable: {last_error}"

    except Exception as exc:
        logger.exception("RAG explanation pipeline encountered an error: %s", exc)
        return f"RAG explanation unavailable: {exc}"