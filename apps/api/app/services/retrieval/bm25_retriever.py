import re
import math
from collections import Counter
from typing import List, Optional
from app.schemas.patent import PatentChunkCreate
from app.services.retrieval.types import RetrievalResult, RetrievalFilters
from app.services.retrieval.metadata_filter import MetadataFilterMatcher


class PureBM25Okapi:
    """Pure Python deterministic fallback BM25Okapi implementation

    ensuring zero external dependency failure mode.
    """

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avg_doc_len = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 1.0
        self.doc_freqs: Counter = Counter()
        self.term_freqs: List[Counter] = []

        for doc in corpus:
            tf = Counter(doc)
            self.term_freqs.append(tf)
            for word in tf.keys():
                self.doc_freqs[word] += 1

        self.idf: dict = {}
        for word, freq in self.doc_freqs.items():
            # Standard Lucene/BM25 IDF formula with smoothing
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        scores = [0.0] * self.corpus_size
        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for doc_idx, tf_counter in enumerate(self.term_freqs):
                freq = tf_counter.get(token, 0)
                if freq == 0:
                    continue
                doc_len = self.doc_lengths[doc_idx]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[doc_idx] += idf_val * (numerator / denominator)
        return scores


class BM25Retriever:
    """Deterministic sparse lexical retrieval engine for patent prior-art chunks."""

    # Tokenizer pattern capturing words, numbers, and technical alphanumeric identifiers
    _TOKEN_REGEX = re.compile(r"\b[a-zA-Z0-9_\-]+\b")

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initializes BM25 retriever with Okapi parameters.

        Defaults:
            k1 = 1.5 (term frequency saturation constant)
            b  = 0.75 (document length penalty constant)
        """
        self.k1 = k1
        self.b = b
        self.chunks: List[PatentChunkCreate] = []
        self._bm25_index: Optional[Any] = None

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Deterministic lowercase word and technical term tokenizer."""
        if not text:
            return []
        return [t.lower() for t in cls._TOKEN_REGEX.findall(text) if len(t) > 1]

    def index_chunks(self, chunks: List[PatentChunkCreate]) -> int:
        """Indexes a list of PatentChunkCreate instances into the BM25 model.

        Returns total count of chunks indexed.
        """
        self.chunks = list(chunks)
        if not self.chunks:
            self._bm25_index = None
            return 0

        tokenized_corpus = [self.tokenize(c.text) for c in self.chunks]

        # Prefer rank_bm25 if available, otherwise pure Python implementation
        try:
            from rank_bm25 import BM25Okapi
            self._bm25_index = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        except ImportError:
            self._bm25_index = PureBM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)

        return len(self.chunks)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[RetrievalFilters] = None,
    ) -> List[RetrievalResult]:
        """Executes sparse BM25 query against indexed chunks with optional metadata filtering."""
        if not self._bm25_index or not self.chunks:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25_index.get_scores(query_tokens)

        # Pair scores with chunks and filter
        scored_candidates = []
        for idx, score in enumerate(scores):
            if score <= 0.0:
                continue
            chunk = self.chunks[idx]
            if MetadataFilterMatcher.matches_chunk(chunk, filters):
                scored_candidates.append((score, chunk))

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        results: List[RetrievalResult] = []
        for rank, (score, chunk) in enumerate(scored_candidates[:top_k], start=1):
            results.append(
                RetrievalResult(
                    patent_number=chunk.patent_number,
                    patent_id=chunk.patent_id,
                    chunk_id=chunk.metadata.get("chunk_id") if chunk.metadata else None,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    section=chunk.section,
                    claim_number=chunk.claim_number,
                    page_number=chunk.page_number,
                    paragraph_id=chunk.paragraph_id,
                    retrieval_method="sparse_bm25",
                    retrieval_score=round(float(score), 4),
                    rank=rank,
                    metadata=chunk.metadata or {},
                )
            )

        return results
