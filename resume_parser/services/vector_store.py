import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from resume_parser.services.embedding_service import embed_text

logger = logging.getLogger(__name__)


def internship_to_text(internship: Dict[str, Any]) -> str:
    fields = [
        ("Internship Title", internship.get("title")),
        ("Company", internship.get("company")),
        ("Description", internship.get("description")),
        ("Required Skills", internship.get("required_skills") or internship.get("skills")),
        ("Preferred Skills", internship.get("preferred_skills")),
        ("Education Requirements", internship.get("education_requirements")),
        ("Experience Requirements", internship.get("experience_requirements")),
        ("Location", internship.get("location")),
        ("Work Mode", internship.get("work_mode")),
        ("Duration", internship.get("duration")),
        ("Other Requirements", internship.get("other_requirements") or internship.get("requirements")),
    ]
    parts = []
    for label, value in fields:
        if isinstance(value, list):
            value = ", ".join(map(str, value))
        if value:
            parts.append(f"{label}: {value}")
    return "\n".join(parts)


class InternshipVectorStore:
    def __init__(self, index_path: Path, metadata_path: Path):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index: Optional[Any] = None
        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[Dict[str, Any]] = []

    @property
    def available(self) -> bool:
        return faiss is not None

    def load(self) -> bool:
        if not self.metadata_path.exists():
            return False

        try:
            self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            if self.available and self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                return True
            
            npy_path = self.index_path.with_suffix(".npy")
            if npy_path.exists():
                self.vectors = np.load(str(npy_path))
                return True
        except Exception as exc:
            logger.error("Failed to load existing index: %s", exc)
        return False

    def build(self, internships: List[Dict[str, Any]]) -> int:
        if not internships:
            raise ValueError("Internship dataset is empty.")

        vectors = []
        valid_metadata = []

        for idx, internship in enumerate(internships):
            try:
                text = internship_to_text(internship)
                raw_vector = embed_text(text)
                vector = np.asarray(raw_vector, dtype="float32")
                norm = np.linalg.norm(vector)
                vector /= max(norm, 1e-12)
                vectors.append(vector)
                valid_metadata.append(internship)
            except Exception as exc:
                logger.error("Failed to embed internship #%d: %s", idx, exc)

        if not vectors:
            raise RuntimeError("Failed to generate embeddings for any internship in the dataset.")

        matrix = np.vstack(vectors).astype("float32")
        self.metadata = valid_metadata
        self.vectors = matrix

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

        if self.available:
            try:
                index = faiss.IndexFlatIP(matrix.shape[1])
                index.add(matrix)
                self.index = index
                faiss.write_index(index, str(self.index_path))
            except Exception as e:
                logger.warning("FAISS indexing failed, saving NumPy fallback: %s", e)
                np.save(str(self.index_path.with_suffix(".npy")), matrix)
        else:
            np.save(str(self.index_path.with_suffix(".npy")), matrix)

        self.metadata_path.write_text(json.dumps(valid_metadata, indent=2), encoding="utf-8")
        return len(valid_metadata)

    def search(self, candidate_text: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.index is None and self.vectors is None:
            if not self.load():
                raise RuntimeError("Internship vector index has not been built yet.")

        raw_vector = embed_text(candidate_text)
        query_vec = np.asarray(raw_vector, dtype="float32")
        norm = np.linalg.norm(query_vec)
        query_vec /= max(norm, 1e-12)

        k = min(top_k, len(self.metadata))
        if k <= 0:
            return []

        # FAISS dimension validation
        if self.index is not None and hasattr(self.index, "d") and self.index.d != query_vec.shape[0]:
            logger.warning(
                "FAISS dimension mismatch: index dimension is %d but query vector dimension is %d",
                self.index.d, query_vec.shape[0]
            )
            raise AssertionError(f"FAISS dimension mismatch: index dimension is {self.index.d} but query vector is {query_vec.shape[0]}")

        # FAISS search
        if self.index is not None:
            try:
                scores, indices = self.index.search(query_vec.reshape(1, -1), k)
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    idx_int = int(idx)
                    if 0 <= idx_int < len(self.metadata):
                        results.append((self.metadata[idx_int], float(score)))
                return results
            except (AssertionError, Exception) as err:
                logger.warning("FAISS search raised error (%s)", err)
                raise

        # NumPy fallback
        if self.vectors is not None:
            if self.vectors.shape[1] != query_vec.shape[0]:
                raise AssertionError(f"NumPy vector dimension mismatch: {self.vectors.shape[1]} vs {query_vec.shape[0]}")
            similarities = np.dot(self.vectors, query_vec)
            top_indices = np.argsort(similarities)[::-1][:k]
            return [(self.metadata[i], float(similarities[i])) for i in top_indices]

        return []