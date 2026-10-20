import uuid
from typing import Dict, Any, Optional
from app.schemas.patent import PatentDocumentBase, PatentChunkBase


# Canonical patent document section names
SECTION_TITLE = "title"
SECTION_ABSTRACT = "abstract"
SECTION_CLAIMS = "claims"
SECTION_DESCRIPTION = "description"
SECTION_BACKGROUND = "background"
SECTION_SUMMARY = "summary"
SECTION_DETAILED_DESCRIPTION = "detailed_description"
SECTION_EMBODIMENTS = "embodiments"
SECTION_IMPLEMENTATION = "implementation"
SECTION_ADVANTAGES = "advantages"
SECTION_APPLICATIONS = "applications"
SECTION_REFERENCES = "references"

CANONICAL_SECTIONS = {
    SECTION_TITLE,
    SECTION_ABSTRACT,
    SECTION_CLAIMS,
    SECTION_DESCRIPTION,
    SECTION_BACKGROUND,
    SECTION_SUMMARY,
    SECTION_DETAILED_DESCRIPTION,
    SECTION_EMBODIMENTS,
    SECTION_IMPLEMENTATION,
    SECTION_ADVANTAGES,
    SECTION_APPLICATIONS,
    SECTION_REFERENCES,
}


def to_supabase_patent_document_row(doc: PatentDocumentBase, doc_uuid: Optional[str] = None) -> Dict[str, Any]:
    """Serializes a canonical PatentDocument into a dictionary strictly matching

    the public.patent_documents table schema in Supabase.
    """
    row_id = doc_uuid or str(uuid.uuid4())
    pub_date_str = str(doc.publication_date) if doc.publication_date else None
    filing_date_str = str(doc.filing_date) if doc.filing_date else None
    priority_date_str = str(doc.priority_date) if doc.priority_date else None

    return {
        "id": row_id,
        "patent_number": doc.patent_number,
        "publication_number": doc.publication_number,
        "application_number": doc.application_number,
        "country_code": doc.country_code,
        "title": doc.title,
        "abstract": doc.abstract,
        "inventors": doc.inventors,
        "assignee": doc.assignee,
        "publication_date": pub_date_str,
        "filing_date": filing_date_str,
        "priority_date": priority_date_str,
        "ipc_classes": doc.ipc_classes,
        "cpc_classes": doc.cpc_classes,
        "language": doc.language,
        "source": doc.source,
        "metadata": doc.metadata,
    }


def to_supabase_patent_chunk_row(chunk: PatentChunkBase, patent_id: str, chunk_uuid: Optional[str] = None) -> Dict[str, Any]:
    """Serializes a canonical PatentChunk into a dictionary strictly matching

    the public.patent_chunks table schema in Supabase.
    """
    return {
        "id": chunk_uuid or str(uuid.uuid4()),
        "patent_id": patent_id,
        "chunk_index": chunk.chunk_index,
        "section": chunk.section,
        "claim_number": chunk.claim_number,
        "page_number": chunk.page_number,
        "paragraph_id": chunk.paragraph_id,
        "text": chunk.text,
        "metadata": chunk.metadata,
        "embedding_status": chunk.embedding_status,
    }
