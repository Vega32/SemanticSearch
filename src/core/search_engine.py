
import re

import faiss
import numpy as np

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

from src.core.index_manager import IndexManager


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

CANDIDATE_K = 20
TOP_K = 8
RRF_K = 60


class SearchEngine:

    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.reranker = CrossEncoder(RERANKER_MODEL)

        self.index_manager = IndexManager()

        self.chunks = []
        self.faiss_index = None
        self.bm25_index = None

    @staticmethod
    def tokenize(text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    def load_index(self, chunks: list[dict]) -> bool:
        """
        Attempt to load a previously saved FAISS index.

        Returns True if the saved index is valid.
        Returns False if it needs to be rebuilt.
        """

        index = self.index_manager.load(
            expected_chunks=chunks,
            embedding_model=EMBEDDING_MODEL
        )

        if index is None:
            return False

        self.chunks = chunks
        self.faiss_index = index

        # BM25 is inexpensive to rebuild compared with embeddings.
        tokenized_documents = [
            self.tokenize(chunk["text"])
            for chunk in self.chunks
        ]

        self.bm25_index = BM25Okapi(tokenized_documents)

        return True

    def build_index(self, chunks: list[dict]) -> None:
        self.chunks = chunks

        if not self.chunks:
            self.faiss_index = None
            self.bm25_index = None
            self.index_manager.clear()
            return

        texts = [
            chunk["text"]
            for chunk in self.chunks
        ]

        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        ).astype("float32")

        embedding_dimension = embeddings.shape[1]

        self.faiss_index = faiss.IndexFlatIP(
            embedding_dimension
        )

        self.faiss_index.add(embeddings)

        tokenized_documents = [
            self.tokenize(text)
            for text in texts
        ]

        self.bm25_index = BM25Okapi(tokenized_documents)

        # Persist the index and its corresponding chunks.
        self.index_manager.save(
            faiss_index=self.faiss_index,
            chunks=self.chunks,
            embedding_model=EMBEDDING_MODEL
        )

    def semantic_search(
        self,
        query: str,
        candidate_k: int = CANDIDATE_K
    ) -> list[dict]:

        if self.faiss_index is None:
            return []

        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        result_count = min(
            candidate_k,
            len(self.chunks)
        )

        scores, indices = self.faiss_index.search(
            query_embedding,
            result_count
        )

        results = []

        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue

            results.append({
                **self.chunks[index],
                "semantic_score": float(score),
                "chunk_id": int(index)
            })

        return results

    def keyword_search(
        self,
        query: str,
        candidate_k: int = CANDIDATE_K
    ) -> list[dict]:

        if self.bm25_index is None:
            return []

        query_tokens = self.tokenize(query)

        if not query_tokens:
            return []

        scores = self.bm25_index.get_scores(query_tokens)

        # Ignore documents that have no keyword matches.
        matching_indices = np.where(scores > 0)[0]

        if len(matching_indices) == 0:
            return []

        ranked_indices = matching_indices[
            np.argsort(scores[matching_indices])[::-1]
        ]

        ranked_indices = ranked_indices[:candidate_k]

        results = []

        for index in ranked_indices:
            results.append({
                **self.chunks[int(index)],
                "keyword_score": float(scores[index]),
                "chunk_id": int(index)
            })

        return results

    def hybrid_search(
        self,
        query: str,
        candidate_k: int = CANDIDATE_K
    ) -> list[dict]:

        semantic_results = self.semantic_search(
            query,
            candidate_k
        )

        keyword_results = self.keyword_search(
            query,
            candidate_k
        )

        candidates = {}

        # Add semantic search rankings.
        for rank, result in enumerate(
            semantic_results,
            start=1
        ):

            chunk_id = result["chunk_id"]

            candidates.setdefault(
                chunk_id,
                {**result, "rrf_score": 0.0}
            )

            candidates[chunk_id]["semantic_rank"] = rank

            candidates[chunk_id]["rrf_score"] += (
                1 / (RRF_K + rank)
            )

        # Add keyword search rankings.
        for rank, result in enumerate(
            keyword_results,
            start=1
        ):

            chunk_id = result["chunk_id"]

            candidates.setdefault(
                chunk_id,
                {**result, "rrf_score": 0.0}
            )

            candidates[chunk_id]["keyword_rank"] = rank

            candidates[chunk_id]["rrf_score"] += (
                1 / (RRF_K + rank)
            )

        return sorted(
            candidates.values(),
            key=lambda result: result["rrf_score"],
            reverse=True
        )

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = TOP_K
    ) -> list[dict]:

        if not candidates:
            return []

        pairs = [
            (query, candidate["text"])
            for candidate in candidates
        ]

        scores = self.reranker.predict(
            pairs,
            batch_size=16,
            show_progress_bar=False
        )

        scores = np.asarray(scores).reshape(-1)

        reranked_results = []

        for candidate, score in zip(candidates, scores):
            reranked_results.append({
                **candidate,
                "rerank_score": float(score)
            })

        reranked_results.sort(
            key=lambda result: result["rerank_score"],
            reverse=True
        )

        return reranked_results[:top_k]

    def search(
        self,
        query: str,
        top_k: int = TOP_K
    ) -> list[dict]:

        if not query.strip():
            return []

        if not self.chunks:
            return []

        candidates = self.hybrid_search(
            query,
            CANDIDATE_K
        )

        return self.rerank(
            query,
            candidates,
            top_k
        )
