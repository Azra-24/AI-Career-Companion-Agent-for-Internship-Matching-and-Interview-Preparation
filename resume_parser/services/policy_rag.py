import os
import json
import logging
import numpy as np
import faiss
from typing import List, Dict, Any
from resume_parser.services.embedding_service import embed_text

logger = logging.getLogger(__name__)

INDEX_DIR = "data/faiss_policy_index"
INDEX_PATH = os.path.join(INDEX_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(INDEX_DIR, "chunks.json")
PDF_PATH = "data/policy.pdf"

_index = None
_chunks = []

def extract_pdf_chunks(pdf_path: str) -> List[str]:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Split text into paragraph-sized blocks
        raw_paragraphs = full_text.split("\n\n")
        chunks = []
        for p in raw_paragraphs:
            p_clean = p.strip()
            if p_clean:
                chunks.append(p_clean)
        return chunks
    except Exception as e:
        logger.error("Failed to extract PDF chunks: %s", e)
        return []

def build_policy_index():
    global _index, _chunks
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    if not os.path.exists(PDF_PATH):
        logger.warning(f"Policy PDF not found at {PDF_PATH}")
        return
        
    logger.info("Extracting chunks from policy PDF...")
    chunks = extract_pdf_chunks(PDF_PATH)
    if not chunks:
        logger.warning("No chunks extracted from policy PDF.")
        return
        
    logger.info(f"Embedding {len(chunks)} chunks...")
    embeddings = []
    valid_chunks = []
    for chunk in chunks:
        try:
            vec = embed_text(chunk)
            embeddings.append(vec)
            valid_chunks.append(chunk)
        except Exception as e:
            logger.error(f"Failed to embed chunk: {e}")
            
    if not embeddings:
        logger.warning("No valid embeddings created.")
        return
        
    embeddings_np = np.array(embeddings, dtype='float32')
    dim = embeddings_np.shape[1]
    
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_np)
    
    # Save FAISS index
    faiss.write_index(index, INDEX_PATH)
    
    # Save chunks mapping
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(valid_chunks, f, indent=2, ensure_ascii=False)
        
    _index = index
    _chunks = valid_chunks
    logger.info("FAISS policy index built and saved successfully.")

def init_policy_rag():
    global _index, _chunks
    if not os.path.exists(INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        build_policy_index()
    else:
        try:
            _index = faiss.read_index(INDEX_PATH)
            with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
                _chunks = json.load(f)
            logger.info("Loaded existing FAISS policy index.")
        except Exception as e:
            logger.error("Failed to load FAISS policy index: %s. Rebuilding...", e)
            build_policy_index()

def retrieve_relevant_chunks(query: str, k: int = 3) -> List[str]:
    global _index, _chunks
    if _index is None or not _chunks:
        init_policy_rag()
        
    if _index is None or not _chunks:
        return []
        
    try:
        query_vec = np.array([embed_text(query)], dtype='float32')
        distances, indices = _index.search(query_vec, k)
        
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(_chunks):
                results.append(_chunks[idx])
        return results
    except Exception as e:
        logger.error("Error retrieving relevant chunks: %s", e)
        return []
