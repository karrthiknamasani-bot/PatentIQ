import re
from typing import List, Optional, Tuple
from app.schemas.patent import PatentDocumentBase, PatentChunkCreate
from app.services.patent_corpus.normalizer import PatentNormalizer
from app.services.patent_corpus.models import (
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
)


class PatentCorpusChunker:
    """Patent-aware chunker that strictly isolates claims, tracks claim numbers,

    and preserves patent section boundaries.
    """

    # Claim start pattern matching "Claim 1.", "Claim 1:", "1.", "(1)", "Patent Claim 1:"
    _CLAIM_BOUNDARY_REGEX = re.compile(
        r"(?:^|\n)(?:(?:patent\s+)?claim\s+(\d+)[:\.\s]|(\d+)[\.:]\s+|(?:\((\d+)\)\s+))",
        re.IGNORECASE,
    )

    # Paragraph ID pattern matching USPTO paragraph numbers like [0001], [0042]
    _PARAGRAPH_ID_REGEX = re.compile(r"(\[\d{4}\])")

    # Section headings within patent description text
    _SECTION_HEADING_PATTERNS = [
        (SECTION_BACKGROUND, re.compile(r"^(?:(?:1\.|i\.)\s*)?(?:background(?:\s+of\s+the\s+invention)?|prior\s+art)\b", re.IGNORECASE)),
        (SECTION_SUMMARY, re.compile(r"^(?:(?:2\.|ii\.)\s*)?(?:brief\s+)?summary(?:\s+of\s+the\s+invention)?\b", re.IGNORECASE)),
        (SECTION_DETAILED_DESCRIPTION, re.compile(r"^(?:(?:3\.|iii\.)\s*)?(?:detailed\s+description(?:\s+of\s+(?:the\s+)?invention)?)\b", re.IGNORECASE)),
        (SECTION_EMBODIMENTS, re.compile(r"^(?:preferred\s+|exemplary\s+)?embodiments?\b", re.IGNORECASE)),
        (SECTION_IMPLEMENTATION, re.compile(r"^(?:system\s+architecture|implementation\s+details)\b", re.IGNORECASE)),
        (SECTION_ADVANTAGES, re.compile(r"^(?:technical\s+)?advantages?(?:\s+of\s+the\s+invention)?\b", re.IGNORECASE)),
        (SECTION_APPLICATIONS, re.compile(r"^(?:industrial\s+applicability|commercial\s+applications?)\b", re.IGNORECASE)),
    ]

    def __init__(self, max_chars: int = 1000, overlap_chars: int = 200) -> None:
        self.max_chars = max(50, max_chars)
        self.overlap_chars = max(0, min(overlap_chars, self.max_chars // 2))

    def chunk_document(self, doc: PatentDocumentBase) -> List[PatentChunkCreate]:
        """Splits a normalized patent document into granular, traceable PatentChunkCreate records."""
        chunks: List[PatentChunkCreate] = []
        chunk_idx = 0

        # Base citation metadata attached to every chunk
        base_meta = {
            "patent_number": doc.patent_number,
            "title": doc.title,
            "country_code": doc.country_code,
            "publication_date": str(doc.publication_date) if doc.publication_date else None,
            "assignee": doc.assignee,
            "source": doc.source,
        }

        # 1. Title Chunk (if substantial)
        if doc.title:
            chunks.append(
                PatentChunkCreate(
                    patent_number=doc.patent_number,
                    chunk_index=chunk_idx,
                    section=SECTION_TITLE,
                    claim_number=None,
                    paragraph_id="title",
                    text=doc.title,
                    metadata={**base_meta, "section": SECTION_TITLE},
                )
            )
            chunk_idx += 1

        # 2. Abstract Chunks
        if doc.abstract:
            abstract_chunks = self._chunk_narrative_text(
                text=doc.abstract,
                section=SECTION_ABSTRACT,
                start_index=chunk_idx,
                patent_number=doc.patent_number,
                base_meta=base_meta,
            )
            chunks.extend(abstract_chunks)
            chunk_idx += len(abstract_chunks)

        # 3. Claims Chunks (Traceable by claim_number)
        if doc.claims:
            claim_chunks = self._chunk_claims(
                claims_data=doc.claims,
                start_index=chunk_idx,
                patent_number=doc.patent_number,
                base_meta=base_meta,
            )
            chunks.extend(claim_chunks)
            chunk_idx += len(claim_chunks)

        # 4. Description Chunks
        if doc.description:
            desc_chunks = self._chunk_description(
                description=doc.description,
                start_index=chunk_idx,
                patent_number=doc.patent_number,
                base_meta=base_meta,
            )
            chunks.extend(desc_chunks)
            chunk_idx += len(desc_chunks)

        return chunks

    def _chunk_claims(
        self,
        claims_data: Union[List[str], str],
        start_index: int,
        patent_number: str,
        base_meta: dict,
    ) -> List[PatentChunkCreate]:
        """Separates and chunks patent claims, ensuring each claim retains its specific claim_number."""
        chunks: List[PatentChunkCreate] = []
        current_idx = start_index

        parsed_claims: List[Tuple[int, str]] = []

        if isinstance(claims_data, list):
            for i, raw_claim in enumerate(claims_data):
                num = self._extract_claim_number(raw_claim) or (i + 1)
                cleaned = PatentNormalizer.clean_text(raw_claim)
                if cleaned:
                    parsed_claims.append((num, cleaned))
        elif isinstance(claims_data, str):
            parsed_claims = self._parse_claims_string(claims_data)

        for claim_num, claim_text in parsed_claims:
            if len(claim_text) <= self.max_chars:
                chunks.append(
                    PatentChunkCreate(
                        patent_number=patent_number,
                        chunk_index=current_idx,
                        section=SECTION_CLAIMS,
                        claim_number=claim_num,
                        paragraph_id=f"claim:{claim_num}",
                        text=claim_text,
                        metadata={**base_meta, "section": SECTION_CLAIMS, "claim_number": claim_num},
                    )
                )
                current_idx += 1
            else:
                # Sub-chunk long claim across sub-clause/sentence boundaries
                sub_chunks = self._split_text_with_overlap(claim_text)
                for part_idx, part_text in enumerate(sub_chunks):
                    chunks.append(
                        PatentChunkCreate(
                            patent_number=patent_number,
                            chunk_index=current_idx,
                            section=SECTION_CLAIMS,
                            claim_number=claim_num,
                            paragraph_id=f"claim:{claim_num}.{part_idx + 1}",
                            text=part_text,
                            metadata={
                                **base_meta,
                                "section": SECTION_CLAIMS,
                                "claim_number": claim_num,
                                "sub_chunk": part_idx + 1,
                            },
                        )
                    )
                    current_idx += 1

        return chunks

    def _parse_claims_string(self, text: str) -> List[Tuple[int, str]]:
        """Parses a continuous claims block into individual (claim_number, claim_text) pairs."""
        matches = list(self._CLAIM_BOUNDARY_REGEX.finditer(text))
        if not matches:
            # Fallback: treat entire block as Claim 1
            return [(1, PatentNormalizer.clean_text(text))]

        parsed = []
        for i, match in enumerate(matches):
            c_num_str = match.group(1) or match.group(2) or match.group(3)
            c_num = int(c_num_str) if c_num_str and c_num_str.isdigit() else (i + 1)

            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            c_body = PatentNormalizer.clean_text(text[start:end])
            if c_body:
                parsed.append((c_num, c_body))

        return parsed

    @classmethod
    def _extract_claim_number(cls, text: str) -> Optional[int]:
        """Extracts claim number from start of claim line if present."""
        m = cls._CLAIM_BOUNDARY_REGEX.match(text.strip())
        if m:
            num_str = m.group(1) or m.group(2) or m.group(3)
            if num_str and num_str.isdigit():
                return int(num_str)
        return None

    def _chunk_description(
        self,
        description: str,
        start_index: int,
        patent_number: str,
        base_meta: dict,
    ) -> List[PatentChunkCreate]:
        """Decomposes patent description body into section-aware chunks."""
        chunks: List[PatentChunkCreate] = []
        current_idx = start_index

        # Split description into paragraphs
        raw_paras = [p.strip() for p in description.split("\n\n") if p.strip()]
        current_section = SECTION_DESCRIPTION
        section_buffer: List[str] = []

        def flush_buffer(sec: str) -> None:
            nonlocal current_idx
            if not section_buffer:
                return
            combined_text = "\n\n".join(section_buffer)
            section_chunks = self._chunk_narrative_text(
                text=combined_text,
                section=sec,
                start_index=current_idx,
                patent_number=patent_number,
                base_meta=base_meta,
            )
            chunks.extend(section_chunks)
            current_idx += len(section_chunks)
            section_buffer.clear()

        for para in raw_paras:
            # Check if this paragraph is a section heading
            detected_sec = self._detect_section_heading(para)
            if detected_sec and detected_sec != current_section:
                flush_buffer(current_section)
                current_section = detected_sec

            section_buffer.append(para)

        flush_buffer(current_section)
        return chunks

    def _detect_section_heading(self, line: str) -> Optional[str]:
        first_line = line.strip().split("\n")[0].strip()
        if len(first_line) > 80:
            return None
        for sec, pattern in self._SECTION_HEADING_PATTERNS:
            if pattern.search(first_line):
                return sec
        return None

    def _chunk_narrative_text(
        self,
        text: str,
        section: str,
        start_index: int,
        patent_number: str,
        base_meta: dict,
    ) -> List[PatentChunkCreate]:
        """Chunks a coherent narrative section using sentence boundary snapping and overlap."""
        chunks: List[PatentChunkCreate] = []
        sub_texts = self._split_text_with_overlap(text)

        for i, sub in enumerate(sub_texts):
            # Extract paragraph ID if present (e.g., [0042])
            para_match = self._PARAGRAPH_ID_REGEX.search(sub)
            para_id = para_match.group(1) if para_match else f"para:{i + 1}"

            chunks.append(
                PatentChunkCreate(
                    patent_number=patent_number,
                    chunk_index=start_index + i,
                    section=section,
                    claim_number=None,
                    paragraph_id=para_id,
                    text=sub,
                    metadata={**base_meta, "section": section},
                )
            )

        return chunks

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """Splits narrative text into slices <= max_chars, snapping to sentence endings where possible."""
        cleaned = PatentNormalizer.clean_text(text)
        if len(cleaned) <= self.max_chars:
            return [cleaned]

        sentences = re.split(r"(?<=[.?!;])\s+", cleaned)
        slices: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If a single sentence exceeds max_chars, split it forcibly
            if len(sentence) > self.max_chars:
                if current_chunk:
                    slices.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                for pos in range(0, len(sentence), self.max_chars - self.overlap_chars):
                    sub_s = sentence[pos : pos + self.max_chars].strip()
                    if sub_s:
                        slices.append(sub_s)
                continue

            if current_len + len(sentence) + 1 > self.max_chars:
                # Flush current chunk
                joined = " ".join(current_chunk)
                slices.append(joined)

                # Overlap: keep trailing sentence(s) up to overlap_chars
                overlap_accum = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) + 1 <= self.overlap_chars:
                        overlap_accum.insert(0, s)
                        overlap_len += len(s) + 1
                    else:
                        break

                current_chunk = overlap_accum + [sentence]
                current_len = sum(len(s) for s in current_chunk) + len(current_chunk) - 1
            else:
                current_chunk.append(sentence)
                current_len += len(sentence) + 1

        if current_chunk:
            slices.append(" ".join(current_chunk))

        return slices
