"""Tests validating complete schema compatibility between FastAPI persistence models

and the Supabase PostgreSQL schema definition and migrations.
"""

import re
from pathlib import Path
import pytest

from app.services.persistence.models import (
    ProjectCreate,
    ProjectRecord,
    DocumentChunkRecord,
    PatentDocumentRecord,
    PatentChunkRecord,
    FeatureRecord,
    EvidenceItemRecord,
    AnalysisRecord,
    ReportRecord,
)
from app.services.mapping.types import EvidenceRelationship


def _find_repo_root() -> Path:
    """Finds repository root relative to this test file."""
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        if (cur / "backend" / "supabase_schema.sql").exists():
            return cur
        cur = cur.parent
    raise FileNotFoundError("Could not find PatentIQ repository root containing backend/supabase_schema.sql")


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return _find_repo_root()


@pytest.fixture(scope="module")
def schema_sql(repo_root: Path) -> str:
    path = repo_root / "backend" / "supabase_schema.sql"
    assert path.exists(), f"Schema file not found at {path}"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def migration_sql(repo_root: Path) -> str:
    path = repo_root / "backend" / "migrations" / "20260916_001_initial_schema_corrected.sql"
    assert path.exists(), f"Migration file not found at {path}"
    return path.read_text(encoding="utf-8")


def _extract_table_columns(sql: str, table_name: str) -> set:
    """Extracts column names defined in a CREATE TABLE public.<table_name> block."""
    pattern = rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.{table_name}\s*\((.*?)\);\s*"
    match = re.search(pattern, sql, re.DOTALL | re.IGNORECASE)
    assert match, f"Table public.{table_name} definition not found in SQL"
    body = match.group(1)

    columns = set()
    for line in body.splitlines():
        line = line.strip()
        # Skip constraints, comments, empty lines
        if not line or line.startswith("--") or re.match(r"^(?:CONSTRAINT|PRIMARY|FOREIGN|CHECK|UNIQUE)\b", line, re.IGNORECASE):
            continue
        # Extract column name (first identifier)
        col_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", line)
        if col_match:
            columns.add(col_match.group(1).lower())
    return columns


def test_schema_files_exist(repo_root: Path):
    """Verifies that the canonical schema and migration files exist."""
    schema_path = repo_root / "backend" / "supabase_schema.sql"
    migration_path = repo_root / "backend" / "migrations" / "20260916_001_initial_schema_corrected.sql"
    assert schema_path.is_file()
    assert migration_path.is_file()
    assert len(schema_path.read_text(encoding="utf-8")) > 1000
    assert len(migration_path.read_text(encoding="utf-8")) > 1000


def test_all_nine_tables_defined(schema_sql: str):
    """Verifies that all 9 required relational tables are defined in the schema."""
    expected_tables = [
        "profiles",
        "projects",
        "document_chunks",
        "patent_documents",
        "patent_chunks",
        "features",
        "evidence_items",
        "analyses",
        "reports",
    ]
    for tbl in expected_tables:
        pattern = rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.{tbl}\b"
        assert re.search(pattern, schema_sql, re.IGNORECASE), f"Missing table public.{tbl} in schema"


@pytest.mark.parametrize(
    "model_cls,table_name,excluded_fields",
    [
        (ProjectRecord, "projects", set()),
        (ProjectCreate, "projects", set()),
        (DocumentChunkRecord, "document_chunks", set()),
        (PatentDocumentRecord, "patent_documents", set()),
        (PatentChunkRecord, "patent_chunks", set()),
        (FeatureRecord, "features", set()),
        (EvidenceItemRecord, "evidence_items", set()),
        (AnalysisRecord, "analyses", set()),
        (ReportRecord, "reports", set()),
    ],
)
def test_pydantic_model_fields_match_sql_columns(schema_sql: str, model_cls, table_name: str, excluded_fields: set):
    """Ensures every field in a Pydantic record model has a corresponding column in the SQL table."""
    columns = _extract_table_columns(schema_sql, table_name)
    model_fields = set(model_cls.model_fields.keys()) - excluded_fields

    missing = model_fields - columns
    assert not missing, f"Model {model_cls.__name__} has fields missing from public.{table_name}: {missing}"


def test_evidence_items_safe_foreign_keys(schema_sql: str, migration_sql: str):
    """CRITICAL TEST: Ensures evidence_items does NOT enforce strict foreign keys on feature_id and patent_id.

    Synthetic UUIDv5s generated during the pipeline must not fail on insertion.
    Project cascading deletion must be preserved via project_id.
    """
    for sql_content, name in [(schema_sql, "supabase_schema.sql"), (migration_sql, "migration script")]:
        match = re.search(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.evidence_items\s*\((.*?)\);\s*",
            sql_content,
            re.DOTALL | re.IGNORECASE,
        )
        assert match, f"evidence_items table definition not found in {name}"
        table_body = match.group(1)

        # evidence_items must not have REFERENCES public.features(id)
        assert not re.search(r"feature_id\s+UUID\s+REFERENCES\s+public\.features", table_body, re.IGNORECASE), (
            f"Hazard in {name}: evidence_items.feature_id must not strictly reference features(id)"
        )
        # evidence_items must not have REFERENCES public.patent_documents(id)
        assert not re.search(r"patent_id\s+UUID\s+REFERENCES\s+public\.patent_documents", table_body, re.IGNORECASE), (
            f"Hazard in {name}: evidence_items.patent_id must not strictly reference patent_documents(id)"
        )
        # project_id MUST reference projects with CASCADE
        assert re.search(r"project_id\s+UUID\s+REFERENCES\s+public\.projects\(id\)\s+ON\s+DELETE\s+CASCADE", table_body, re.IGNORECASE), (
            f"Missing cascade foreign key on project_id in {name}"
        )


def test_unique_constraints_for_upserts(schema_sql: str):
    """Verifies that all unique constraints required for repository upsert operations exist."""
    # features upsert requires (project_id, feature_id)
    assert re.search(r"UNIQUE\s*\(\s*project_id\s*,\s*feature_id\s*\)", schema_sql, re.IGNORECASE)
    # patent_documents upsert requires patent_number UNIQUE
    assert re.search(r"patent_number\s+TEXT\s+UNIQUE", schema_sql, re.IGNORECASE)
    # reports upsert/idempotency requires (project_id, type)
    assert re.search(r"UNIQUE\s*\(\s*project_id\s*,\s*type\s*\)", schema_sql, re.IGNORECASE)


def test_evidence_relationship_enum_values_in_check_constraint(schema_sql: str):
    """Verifies all EvidenceRelationship enum values are allowed by the CHECK constraint."""
    match = re.search(r"evidence_relationship\s+IN\s*\((.*?)\)", schema_sql, re.DOTALL | re.IGNORECASE)
    assert match, "CHECK constraint for evidence_relationship not found"
    constraint_str = match.group(1)

    for enum_member in EvidenceRelationship:
        assert f"'{enum_member.value}'" in constraint_str, (
            f"Enum value '{enum_member.value}' not present in evidence_relationship CHECK constraint"
        )


def test_rls_enabled_and_policies_enforced(schema_sql: str):
    """Verifies RLS enablement and WITH CHECK policy enforcement across user tables."""
    user_tables = [
        "profiles",
        "projects",
        "document_chunks",
        "features",
        "analyses",
        "evidence_items",
        "reports",
    ]
    for tbl in user_tables:
        assert f"ALTER TABLE public.{tbl} ENABLE ROW LEVEL SECURITY;" in schema_sql
        # Check that both USING and WITH CHECK exist in the policy
        pattern = rf'CREATE\s+POLICY\s+"[^"]+"\s+ON\s+public\.{tbl}\s+FOR\s+ALL.*?USING\s*\(.*?\)\s*WITH\s+CHECK\s*\('
        assert re.search(pattern, schema_sql, re.DOTALL | re.IGNORECASE), (
            f"Table public.{tbl} missing strict USING + WITH CHECK RLS policy"
        )

    # Patent tables should have SELECT only
    for tbl in ["patent_documents", "patent_chunks"]:
        assert f"ALTER TABLE public.{tbl} ENABLE ROW LEVEL SECURITY;" in schema_sql
        pattern = rf'CREATE\s+POLICY\s+"[^"]+"\s+ON\s+public\.{tbl}\s+FOR\s+SELECT\s+TO\s+authenticated,\s*anon'
        assert re.search(pattern, schema_sql, re.IGNORECASE)


def test_no_pgvector_extensions(schema_sql: str, migration_sql: str):
    """Verifies that pgvector is NOT enabled in PostgreSQL (Qdrant handles all vectors)."""
    for sql_content in [schema_sql, migration_sql]:
        assert "vector" not in sql_content.lower() or "uuid-ossp" in sql_content
        assert "create extension if not exists vector" not in sql_content.lower()
        assert "create extension if not exists \"vector\"" not in sql_content.lower()
