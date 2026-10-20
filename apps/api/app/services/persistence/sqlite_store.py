"""Durable local SQLite persistence store for PatentIQ.

Provides ACID durable storage surviving server restarts when Supabase credentials
are not configured. Stores projects, document chunks, features, evidence items,
analyses, reports, user profiles, and active sessions at data/patentiq_local.db.
"""

import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("patentiq.persistence.sqlite")

# Default database location relative to repository root
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
DEFAULT_DB_PATH = os.path.join(REPO_ROOT, "data", "patentiq_local.db")


def _json_serialize(obj: Any) -> str:
    """Helper to serialize dict/list fields into JSON strings safely."""
    if obj is None:
        return "{}"
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, default=str)


def _json_deserialize(val: Any) -> Any:
    """Helper to parse JSON fields safely."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return val


class SQLiteStore:
    """Thread-safe SQLite persistent store with WAL mode and foreign keys enabled."""

    _instance: Optional["SQLiteStore"] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Retrieves or creates a thread-local SQLite connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=20.0,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA foreign_keys=ON;")
            self._local.conn = conn
        return self._local.conn

    def _init_schema(self) -> None:
        """Provisions schema tables matching PatentIQ entities idempotently."""
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    email TEXT,
                    name TEXT,
                    created_at TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT,
                    name TEXT,
                    created_at TEXT,
                    expires_at TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    original_file_name TEXT NOT NULL,
                    stored_file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    status TEXT DEFAULT 'uploaded',
                    processing_stage TEXT DEFAULT 'uploaded',
                    extracted_text TEXT,
                    extracted_metadata TEXT DEFAULT '{}',
                    error_message TEXT,
                    report_generated INTEGER DEFAULT 0,
                    progress INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    section TEXT DEFAULT 'unknown',
                    page_number INTEGER,
                    source_reference TEXT,
                    text TEXT NOT NULL,
                    start_character INTEGER DEFAULT 0,
                    end_character INTEGER DEFAULT 0,
                    token_estimate INTEGER DEFAULT 0,
                    embedding_status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS features (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    feature_id TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    technical_category TEXT,
                    importance TEXT DEFAULT 'medium',
                    source_text_span TEXT,
                    extraction_confidence REAL DEFAULT 1.0,
                    created_at TEXT,
                    UNIQUE(project_id, feature_id),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_items (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    feature_id TEXT NOT NULL,
                    patent_id TEXT NOT NULL,
                    chunk_text TEXT,
                    retrieved_source TEXT,
                    retrieval_method TEXT DEFAULT 'hybrid_rrf',
                    retrieval_similarity REAL DEFAULT 0.0,
                    reranker_score REAL,
                    rank INTEGER,
                    section TEXT,
                    claim_number INTEGER,
                    page_number INTEGER,
                    evidence_strength REAL DEFAULT 0.0,
                    confidence REAL DEFAULT 1.0,
                    evidence_relationship TEXT,
                    created_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL UNIQUE,
                    readiness_score INTEGER NOT NULL,
                    confidence_score REAL NOT NULL,
                    readiness_category TEXT NOT NULL,
                    novelty_score INTEGER NOT NULL,
                    overlap_score INTEGER NOT NULL,
                    differentiation_score INTEGER NOT NULL,
                    documentation_score INTEGER NOT NULL,
                    innovation_characteristics TEXT DEFAULT '{}',
                    commercial_potential TEXT DEFAULT '{}',
                    explanation TEXT,
                    recommendations TEXT DEFAULT '[]',
                    uncertainty_flags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    model_used TEXT,
                    processing_time INTEGER DEFAULT 0,
                    retrieved_chunk_count INTEGER DEFAULT 0,
                    retrieved_patents TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'completed',
                    created_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    type TEXT DEFAULT 'json',
                    file_path TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT,
                    UNIQUE(project_id, type),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                """
            )
        logger.info("SQLite schema initialized successfully at %s", self.db_path)

    def is_ready(self) -> bool:
        """Returns True if the SQLite database is reachable and tables exist."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects';")
            row = cur.fetchone()
            return row is not None
        except Exception:
            return False

    # =========================================================================
    # User Profile & Sessions (Google OAuth & Demo)
    # =========================================================================

    def upsert_user_profile(self, user_id: str, email: str, name: Optional[str] = None) -> Dict[str, Any]:
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute(
                """
                INSERT INTO profiles (id, email, name, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    email = excluded.email,
                    name = coalesce(excluded.name, profiles.name);
                """,
                (user_id, email, name or email.split("@")[0], now),
            )
        return {"id": user_id, "email": email, "name": name}

    def create_session(self, token: str, user_id: str, email: str, name: Optional[str] = None, expires_at: Optional[str] = None) -> None:
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute(
                """
                INSERT INTO sessions (token, user_id, email, name, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(token) DO UPDATE SET
                    user_id = excluded.user_id,
                    email = excluded.email,
                    name = excluded.name;
                """,
                (token, user_id, email, name or email.split("@")[0], now, expires_at),
            )

    def get_session_user(self, token: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, email, name FROM sessions WHERE token = ?", (token,))
        row = cur.fetchone()
        if row:
            return {"user_id": row["user_id"], "email": row["email"], "name": row["name"]}
        return None

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, created_at FROM profiles WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return {"id": row["id"], "email": row["email"], "name": row["name"], "created_at": row["created_at"]}
        return None

    # =========================================================================
    # 1. Projects
    # =========================================================================

    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._get_connection()
        now_str = (data.get("created_at") or datetime.now(timezone.utc)).isoformat() if isinstance(data.get("created_at"), datetime) else str(data.get("created_at") or datetime.now(timezone.utc).isoformat())
        with conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, user_id, title, description, original_file_name,
                    stored_file_name, file_path, file_type, file_size,
                    status, processing_stage, extracted_text, extracted_metadata,
                    error_message, report_generated, progress, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["user_id"],
                    data["title"],
                    data.get("description"),
                    data["original_file_name"],
                    data["stored_file_name"],
                    data["file_path"],
                    data["file_type"],
                    int(data["file_size"]),
                    data.get("status", "uploaded"),
                    data.get("processing_stage", "uploaded"),
                    data.get("extracted_text"),
                    _json_serialize(data.get("extracted_metadata", {})),
                    data.get("error_message"),
                    1 if data.get("report_generated") else 0,
                    int(data.get("progress", 0)),
                    now_str,
                    now_str,
                ),
            )
        return self.get_project(data["id"], data["user_id"]) or data

    def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["extracted_metadata"] = _json_deserialize(res.get("extracted_metadata"))
        res["report_generated"] = bool(res.get("report_generated"))
        return res

    def list_projects(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM projects
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()
        projects = []
        for r in rows:
            p = dict(r)
            p["extracted_metadata"] = _json_deserialize(p.get("extracted_metadata"))
            p["report_generated"] = bool(p.get("report_generated"))
            projects.append(p)
        return projects

    def delete_project(self, project_id: str, user_id: str) -> bool:
        conn = self._get_connection()
        with conn:
            cur = conn.execute(
                "DELETE FROM projects WHERE id = ? AND user_id = ?",
                (project_id, user_id),
            )
            return cur.rowcount > 0

    # =========================================================================
    # 2. Document Chunks
    # =========================================================================

    def save_document_chunks(self, project_id: str, chunks: List[Dict[str, Any]]) -> int:
        conn = self._get_connection()
        now_str = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute("DELETE FROM document_chunks WHERE project_id = ?", (project_id,))
            for i, c in enumerate(chunks):
                chunk_id = c.get("id") or f"{project_id}_{c.get('chunk_index', i)}"
                conn.execute(
                    """
                    INSERT INTO document_chunks (
                        id, project_id, chunk_index, section, page_number,
                        source_reference, text, start_character, end_character,
                        token_estimate, embedding_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        project_id,
                        c.get("chunk_index", i),
                        c.get("section", "unknown"),
                        c.get("page_number"),
                        c.get("source_reference"),
                        c.get("text", ""),
                        c.get("start_character", 0),
                        c.get("end_character", len(c.get("text", ""))),
                        c.get("token_estimate", 0),
                        "synced" if c.get("embedding_synced") else "pending",
                        now_str,
                    ),
                )
        return len(chunks)

    def get_document_chunks(self, project_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM document_chunks WHERE project_id = ? ORDER BY chunk_index ASC",
            (project_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    # =========================================================================
    # 3. Features
    # =========================================================================

    def save_features(self, project_id: str, features: List[Dict[str, Any]]) -> int:
        conn = self._get_connection()
        now_str = datetime.now(timezone.utc).isoformat()
        with conn:
            for feat in features:
                f_id = feat.get("feature_id") or "f-0"
                row_id = f"{project_id}_{f_id}"
                conn.execute(
                    """
                    INSERT INTO features (
                        id, project_id, feature_id, title, description,
                        technical_category, importance, source_text_span,
                        extraction_confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, feature_id) DO UPDATE SET
                        title = excluded.title,
                        description = excluded.description,
                        technical_category = excluded.technical_category,
                        importance = excluded.importance,
                        source_text_span = excluded.source_text_span,
                        extraction_confidence = excluded.extraction_confidence;
                    """,
                    (
                        row_id,
                        project_id,
                        f_id,
                        feat.get("title") or feat.get("feature_text", "")[:120],
                        feat.get("description") or feat.get("feature_text", ""),
                        feat.get("technical_category") or str(feat.get("feature_type", "structural")),
                        feat.get("importance", "medium"),
                        feat.get("source_text_span") or feat.get("feature_text", ""),
                        float(feat.get("extraction_confidence", feat.get("confidence", 1.0))),
                        now_str,
                    ),
                )
        return len(features)

    def get_features(self, project_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM features WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    # =========================================================================
    # 4. Evidence Items
    # =========================================================================

    def save_evidence_items(self, project_id: str, items: List[Dict[str, Any]]) -> int:
        conn = self._get_connection()
        now_str = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute("DELETE FROM evidence_items WHERE project_id = ?", (project_id,))
            for idx, item in enumerate(items):
                row_id = item.get("id") or f"{project_id}_{item.get('feature_id', 'f')}_{idx}_{uuid.uuid4().hex[:6]}"
                conn.execute(
                    """
                    INSERT INTO evidence_items (
                        id, project_id, feature_id, patent_id, chunk_text,
                        retrieved_source, retrieval_method, retrieval_similarity,
                        reranker_score, rank, section, claim_number, page_number,
                        evidence_strength, confidence, evidence_relationship, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row_id,
                        project_id,
                        str(item.get("feature_id", "f-0")),
                        str(item.get("patent_id") or item.get("patent_number", "UNKNOWN")),
                        item.get("chunk_text") or item.get("evidence_text", ""),
                        item.get("retrieved_source") or item.get("patent_number", "UNKNOWN"),
                        item.get("retrieval_method", "hybrid_rrf"),
                        float(item.get("retrieval_similarity") or item.get("semantic_similarity", 0.0)),
                        float(item["reranker_score"]) if item.get("reranker_score") is not None else None,
                        item.get("rank") or item.get("reranker_rank"),
                        item.get("section"),
                        item.get("claim_number"),
                        item.get("page_number"),
                        float(item.get("evidence_strength") or item.get("matching_score", 0.0)),
                        float(item.get("confidence") or item.get("mapping_confidence", 1.0)),
                        str(item.get("evidence_relationship", "contextual_match")),
                        now_str,
                    ),
                )
        return len(items)

    def get_evidence_items(self, project_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM evidence_items WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    # =========================================================================
    # 5. Analyses (EB-PRE Exact Preserved Scores)
    # =========================================================================

    def save_analysis(self, project_id: str, row: Dict[str, Any]) -> str:
        conn = self._get_connection()
        now_str = datetime.now(timezone.utc).isoformat()
        rec_id = row.get("id") or f"ana_{project_id}"
        with conn:
            conn.execute("DELETE FROM analyses WHERE project_id = ?", (project_id,))
            conn.execute(
                """
                INSERT INTO analyses (
                    id, project_id, readiness_score, confidence_score,
                    readiness_category, novelty_score, overlap_score,
                    differentiation_score, documentation_score,
                    innovation_characteristics, commercial_potential,
                    explanation, recommendations, uncertainty_flags,
                    metadata, model_used, processing_time, retrieved_chunk_count,
                    retrieved_patents, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec_id,
                    project_id,
                    int(row["readiness_score"]),
                    float(row["confidence_score"]),
                    str(row["readiness_category"]),
                    int(row["novelty_score"]),
                    int(row["overlap_score"]),
                    int(row["differentiation_score"]),
                    int(row["documentation_score"]),
                    _json_serialize(row.get("innovation_characteristics", {})),
                    _json_serialize(row.get("commercial_potential", {})),
                    row.get("explanation", ""),
                    _json_serialize(row.get("recommendations", [])),
                    _json_serialize(row.get("uncertainty_flags", [])),
                    _json_serialize(row.get("metadata", {})),
                    row.get("model_used", "deterministic_eb_pre"),
                    int(row.get("processing_time", 0)),
                    int(row.get("retrieved_chunk_count", 0)),
                    _json_serialize(row.get("retrieved_patents", [])),
                    row.get("status", "completed"),
                    now_str,
                ),
            )
        return rec_id

    def get_analysis(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM analyses WHERE project_id = ? ORDER BY created_at DESC LIMIT 1", (project_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["innovation_characteristics"] = _json_deserialize(res.get("innovation_characteristics"))
        res["commercial_potential"] = _json_deserialize(res.get("commercial_potential"))
        res["recommendations"] = _json_deserialize(res.get("recommendations"))
        res["uncertainty_flags"] = _json_deserialize(res.get("uncertainty_flags"))
        res["metadata"] = _json_deserialize(res.get("metadata"))
        res["retrieved_patents"] = _json_deserialize(res.get("retrieved_patents"))
        return res

    # =========================================================================
    # 6. Reports
    # =========================================================================

    def save_report(self, project_id: str, report_type: str, row: Dict[str, Any]) -> str:
        conn = self._get_connection()
        now_str = datetime.now(timezone.utc).isoformat()
        rec_id = row.get("id") or f"rep_{project_id}_{report_type}"
        with conn:
            conn.execute(
                """
                INSERT INTO reports (id, project_id, type, file_path, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, type) DO UPDATE SET
                    file_path = excluded.file_path,
                    metadata = excluded.metadata,
                    created_at = excluded.created_at;
                """,
                (
                    rec_id,
                    project_id,
                    report_type,
                    row.get("file_path", f"projects/{project_id}/reports/report_{report_type}.json"),
                    _json_serialize(row.get("metadata", {})),
                    now_str,
                ),
            )
        return rec_id

    def get_report(self, project_id: str, report_type: str = "json") -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reports WHERE project_id = ? AND type = ?", (project_id, report_type))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["metadata"] = _json_deserialize(res.get("metadata"))
        return res


def get_sqlite_store() -> SQLiteStore:
    """Returns singleton SQLiteStore instance."""
    with SQLiteStore._lock:
        if SQLiteStore._instance is None:
            SQLiteStore._instance = SQLiteStore()
        return SQLiteStore._instance
