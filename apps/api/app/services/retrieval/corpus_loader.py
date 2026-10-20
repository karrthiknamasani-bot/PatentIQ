import os
import json
from typing import List, Iterator, Optional
from app.schemas.patent import PatentChunkCreate


def get_default_corpus_path() -> str:
    """Returns absolute path to canonical chunks (USPTO pilot corpus preferred if present)."""
    # From apps/api/app/services/retrieval/corpus_loader.py -> root is 5 levels up
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
    pilot_path = os.path.join(base_dir, "data", "real_patents_pilot", "chunks", "pilot_chunks.jsonl")
    if os.path.isfile(pilot_path):
        return pilot_path
    return os.path.join(base_dir, "data", "corpus", "sample", "sample_chunks.jsonl")


class RetrievalCorpusLoader:
    """Loads and streams canonical prior-art patent chunks for indexing into

    BM25 and Qdrant vector store.
    """

    @classmethod
    def load_chunks(cls, filepath: Optional[str] = None) -> List[PatentChunkCreate]:
        """Loads all chunks from the canonical JSONL file into memory."""
        path = filepath or get_default_corpus_path()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Prior-art corpus chunks not found at: {path}")

        chunks: List[PatentChunkCreate] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                chunks.append(PatentChunkCreate.model_validate(data))

        return chunks

    @classmethod
    def stream_chunks(cls, filepath: Optional[str] = None) -> Iterator[PatentChunkCreate]:
        """Streams patent chunks one-by-one from the canonical JSONL file."""
        path = filepath or get_default_corpus_path()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Prior-art corpus chunks not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                yield PatentChunkCreate.model_validate(data)
