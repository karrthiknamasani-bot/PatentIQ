from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("apps/api/.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "PatentIQ API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"

    # Deterministic development / demo credentials
    DEMO_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    DEMO_USER_EMAIL: str = "demo.innovator@patentiq.local"
    DEMO_BEARER_TOKEN: str = "patentiq-dev-demo-token-00000000-0000-0000-0000-000000000001"
    GOOGLE_CLIENT_ID: Optional[str] = "835474657730-d6o5fecuacrma2abg2fd9d887mad072b.apps.googleusercontent.com"

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Document Processing Configuration
    MAX_UPLOAD_SIZE_MB: int = 50
    CHUNK_MAX_CHARS: int = 1000
    CHUNK_OVERLAP_CHARS: int = 200
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]

    # Supabase credentials
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # AI / LLM (Gemini 3.1 Pro Preview)
    GEMINI_API_KEY: Optional[str] = None

    # Vector Database (Qdrant)
    QDRANT_URL: Optional[str] = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "patent_prior_art_pilot_uspto2016"
    QDRANT_STORAGE_PATH: Optional[str] = "data/real_patents_pilot/qdrant_db"

    # Sparse Lexical Retrieval (BM25)
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    DEFAULT_RETRIEVAL_TOP_K: int = 10

    # Dense Semantic Retrieval (BGE)
    BGE_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
    BGE_NORMALIZE_EMBEDDINGS: bool = True
    BGE_DIMENSION: int = 768

    # Reciprocal Rank Fusion (RRF)
    RRF_K: int = 60
    RRF_CANDIDATE_DEPTH: int = 20

    # BGE Cross-Encoder Reranker
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-base"
    RERANKER_BATCH_SIZE: int = 8
    RERANKER_CANDIDATE_DEPTH: int = 6

    # Feature-to-Evidence Mapping
    MAPPING_LEXICAL_WEIGHT: float = 0.4
    MAPPING_SEMANTIC_WEIGHT: float = 0.6
    MAPPING_TOP_K: int = 5
    DIRECT_MATCH_THRESHOLD: float = 0.75
    PARTIAL_MATCH_THRESHOLD: float = 0.50
    CONTEXTUAL_MATCH_THRESHOLD: float = 0.30
    WEAK_MATCH_THRESHOLD: float = 0.15

    # Evidence-Based Patent Readiness Engine (EB-PRE)
    READINESS_WEIGHT_NOVELTY: float = 0.30
    READINESS_WEIGHT_PRIOR_ART_OVERLAP: float = 0.20
    READINESS_WEIGHT_TECH_DIFFERENTIATION: float = 0.20
    READINESS_WEIGHT_INNOVATION_CHARS: float = 0.15
    READINESS_WEIGHT_DOC_QUALITY: float = 0.10
    READINESS_WEIGHT_COMMERCIAL_POTENTIAL: float = 0.05
    READINESS_THRESHOLD_MODERATE: float = 0.40
    READINESS_THRESHOLD_HIGH: float = 0.70

    # Grounded Gemini Explanation & Reporting
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_EXPLANATION_MODEL: str = "gemini-3.1-pro-preview"
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    EXPLANATION_MAX_EVIDENCE_ITEMS: int = 15


settings = Settings()
