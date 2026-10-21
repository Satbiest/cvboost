"""Lazy, singleton SBERT encoder. Long documents are token-chunked, not truncated."""
from threading import Lock
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config import BASE_DIR
from services.errors import AppError


class SemanticEncoder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._lock = Lock()

    def _document_vector(self, model, text: str) -> np.ndarray:
        tokens = model.tokenizer.encode(text, add_special_tokens=False)
        window = min(int(model.max_seq_length) - 2, 254)
        stride = max(window - 32, 1)
        chunks, weights = [], []
        for start in range(0, len(tokens), stride):
            chunk = tokens[start:start + window]
            chunks.append(model.tokenizer.decode(chunk, skip_special_tokens=True))
            # Weight only newly covered tokens; do not double-count final overlap.
            weights.append(len(chunk) if start == 0 else max(1, len(chunk) - (window - stride)))
            if start + window >= len(tokens):
                break
        if not chunks:
            raise AppError(422, 'empty_embedding', 'A document has no text to compare.')
        vectors = model.encode(chunks, batch_size=16, normalize_embeddings=True,
                               convert_to_numpy=True, show_progress_bar=False)
        mean = np.average(vectors, axis=0, weights=weights)
        return mean / max(np.linalg.norm(mean), 1e-12)

    def score(self, resume: str, job: str) -> float:
        with self._lock:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(self.model_name, device='cpu', trust_remote_code=False,
                        cache_folder=str(BASE_DIR / '.cache' / 'models'), token=False)
                except Exception:
                    raise AppError(503, 'embedding_unavailable', 'The semantic model could not be loaded. Install requirements.txt and allow the initial model download on the server.') from None
            try:
                vectors = np.stack([self._document_vector(self._model, resume), self._document_vector(self._model, job)])
                similarity = float(cosine_similarity(vectors[:1], vectors[1:])[0, 0])
                return max(0.0, min(1.0, similarity)) * 100
            except AppError:
                raise
            except Exception:
                raise AppError(503, 'embedding_failed', 'The semantic comparison could not be completed. Please try again.') from None

