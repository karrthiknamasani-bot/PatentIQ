import math
import re
from typing import List, Optional, Tuple
from app.core.config import settings
from app.schemas.document import DocumentChunk, ExtractedSegment


class PatentAwareChunker:
    """Structure-aware chunker that respects section boundaries, paragraphs, and patent claims."""

    # Regex patterns for detecting patent claims
    CLAIM_START_REGEX = re.compile(
        r"^(?:(?:patent\s+)?claim\s+(\d+)|(\d+)\.|\((\d+)\)|(\d+)\))\s*[:-]?\s*(.*)$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        max_chars: Optional[int] = None,
        overlap_chars: Optional[int] = None,
    ) -> None:
        self.max_chars = max_chars or settings.CHUNK_MAX_CHARS
        self.overlap_chars = overlap_chars or settings.CHUNK_OVERLAP_CHARS

    @classmethod
    def detect_claim_number(cls, text: str, is_claims_section: bool = False) -> Tuple[Optional[int], str]:
        """Detects if a text block starts with a claim designator.

        Returns (claim_number, remaining_text) if found, else (None, text).
        """
        first_line = text.strip().split("\n")[0].strip() if text else ""
        match = cls.CLAIM_START_REGEX.match(first_line)
        if match:
            # Group 1: "Claim X"
            # Group 2: "X."
            # Group 3: "(X)"
            # Group 4: "X)"
            num_str = match.group(1) or match.group(2) or match.group(3) or match.group(4)
            # If not explicitly in a claims section and it's just "1.", verify it's likely a claim
            if not is_claims_section and not match.group(1):
                # Only treat as claim if "claim" keyword or in claims context
                if "claim" not in first_line.lower():
                    return None, text

            try:
                claim_num = int(num_str)
                return claim_num, text
            except (ValueError, TypeError):
                return None, text

        return None, text

    def chunk_document(self, segments: List[ExtractedSegment]) -> List[DocumentChunk]:
        """Generates patent-aware chunks from extracted document segments."""
        chunks: List[DocumentChunk] = []
        global_char_offset = 0
        chunk_idx = 0

        # Group segments by section to prevent chunk bleeding across sections
        section_groups: List[List[ExtractedSegment]] = []
        current_group: List[ExtractedSegment] = []
        current_section = None

        for seg in segments:
            if current_section is None:
                current_section = seg.section
                current_group.append(seg)
            elif seg.section == current_section:
                current_group.append(seg)
            else:
                section_groups.append(current_group)
                current_group = [seg]
                current_section = seg.section
        if current_group:
            section_groups.append(current_group)

        for group in section_groups:
            sec_name = group[0].section if group else "unknown"
            is_claims_sec = (sec_name == "claims")

            if is_claims_sec:
                # Process claims with special boundary preservation
                claim_chunks, new_offset, chunk_idx = self._chunk_claims_section(
                    group, global_char_offset, chunk_idx
                )
                chunks.extend(claim_chunks)
                global_char_offset = new_offset
            else:
                # Process regular technical narrative sections
                norm_chunks, new_offset, chunk_idx = self._chunk_narrative_section(
                    group, sec_name, global_char_offset, chunk_idx
                )
                chunks.extend(norm_chunks)
                global_char_offset = new_offset

        return chunks

    def _chunk_claims_section(
        self,
        segments: List[ExtractedSegment],
        base_offset: int,
        start_chunk_idx: int,
    ) -> Tuple[List[DocumentChunk], int, int]:
        """Splits claims section keeping each claim intact whenever possible."""
        chunks: List[DocumentChunk] = []
        current_offset = base_offset
        chunk_idx = start_chunk_idx

        # Combine text of segments in this claims section while retaining page references
        full_claims_text = "\n\n".join(s.text for s in segments)
        primary_page = segments[0].page_number if segments else None
        primary_ref = segments[0].source_reference if segments else None

        # Split into blocks by double newlines or claim markers
        lines = full_claims_text.split("\n")
        claim_blocks: List[Tuple[Optional[int], str, Optional[int]]] = []
        current_claim_num = None
        current_claim_lines: List[str] = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            detected_claim, _ = self.detect_claim_number(trimmed, is_claims_section=True)
            if detected_claim is not None:
                if current_claim_lines:
                    claim_blocks.append((current_claim_num, "\n".join(current_claim_lines), primary_page))
                    current_claim_lines = []
                current_claim_num = detected_claim
                current_claim_lines.append(trimmed)
            else:
                current_claim_lines.append(trimmed)

        if current_claim_lines:
            claim_blocks.append((current_claim_num, "\n".join(current_claim_lines), primary_page))

        # Turn each claim block into chunks
        for c_num, text_block, pg in claim_blocks:
            if len(text_block) <= self.max_chars:
                token_est = max(1, math.ceil(len(text_block) / 4))
                end_offset = current_offset + len(text_block)
                chunks.append(
                    DocumentChunk(
                        chunk_index=chunk_idx,
                        text=text_block,
                        section="claims",
                        page_number=pg,
                        claim_number=c_num,
                        source_reference=f"claim:{c_num}" if c_num else primary_ref,
                        start_character=current_offset,
                        end_character=end_offset,
                        token_estimate=token_est,
                    )
                )
                chunk_idx += 1
                current_offset = end_offset + 2
            else:
                # Claim is exceptionally long: break it at semicolons or sentence boundaries
                sub_chunks, current_offset, chunk_idx = self._split_long_text(
                    text=text_block,
                    section="claims",
                    page_number=pg,
                    claim_number=c_num,
                    source_ref=f"claim:{c_num}" if c_num else primary_ref,
                    current_offset=current_offset,
                    start_chunk_idx=chunk_idx,
                )
                chunks.extend(sub_chunks)

        return chunks, current_offset, chunk_idx

    def _chunk_narrative_section(
        self,
        segments: List[ExtractedSegment],
        section_name: str,
        base_offset: int,
        start_chunk_idx: int,
    ) -> Tuple[List[DocumentChunk], int, int]:
        """Chunks technical narrative sections respecting paragraph and sentence boundaries."""
        chunks: List[DocumentChunk] = []
        current_offset = base_offset
        chunk_idx = start_chunk_idx

        for seg in segments:
            text = seg.text
            if not text:
                continue

            # Check if this segment can fit as a single chunk
            if len(text) <= self.max_chars:
                token_est = max(1, math.ceil(len(text) / 4))
                end_offset = current_offset + len(text)
                chunks.append(
                    DocumentChunk(
                        chunk_index=chunk_idx,
                        text=text,
                        section=section_name,
                        page_number=seg.page_number,
                        claim_number=None,
                        source_reference=seg.source_reference,
                        start_character=current_offset,
                        end_character=end_offset,
                        token_estimate=token_est,
                    )
                )
                chunk_idx += 1
                current_offset = end_offset + 2
            else:
                sub_chunks, current_offset, chunk_idx = self._split_long_text(
                    text=text,
                    section=section_name,
                    page_number=seg.page_number,
                    claim_number=None,
                    source_ref=seg.source_reference,
                    current_offset=current_offset,
                    start_chunk_idx=chunk_idx,
                )
                chunks.extend(sub_chunks)

        return chunks, current_offset, chunk_idx

    def _split_long_text(
        self,
        text: str,
        section: str,
        page_number: Optional[int],
        claim_number: Optional[int],
        source_ref: Optional[str],
        current_offset: int,
        start_chunk_idx: int,
    ) -> Tuple[List[DocumentChunk], int, int]:
        """Splits long text into overlapping chunks snapping to sentence boundaries."""
        chunks: List[DocumentChunk] = []
        chunk_idx = start_chunk_idx
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.max_chars
            if end >= text_len:
                end = text_len
            else:
                # Snap to sentence end, newline, or space
                snap_pos = -1
                for delim in [";\n", ".\n", ". ", "; ", "\n\n", "\n", " "]:
                    idx = text.rfind(delim, start + self.overlap_chars, end)
                    if idx != -1:
                        snap_pos = idx + len(delim)
                        break
                if snap_pos != -1:
                    end = snap_pos

            chunk_text = text[start:end].strip()
            if chunk_text:
                token_est = max(1, math.ceil(len(chunk_text) / 4))
                abs_start = current_offset + start
                abs_end = current_offset + end
                chunks.append(
                    DocumentChunk(
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        section=section,
                        page_number=page_number,
                        claim_number=claim_number,
                        source_reference=source_ref,
                        start_character=abs_start,
                        end_character=abs_end,
                        token_estimate=token_est,
                    )
                )
                chunk_idx += 1

            if end >= text_len:
                break

            # Advance by step (accounting for overlap)
            next_start = end - self.overlap_chars
            if next_start <= start:
                start = end
            else:
                start = next_start

        return chunks, current_offset + text_len + 2, chunk_idx
