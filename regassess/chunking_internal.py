"""Chunk the synthetic internal policies (data/internal/KST-*.md) by heading.

Deliberately simpler than regassess/chunking.py: the policies are our own clean
markdown, so a heading walk is enough. No clause-number inference is needed.
"""

import re
from pathlib import Path

from regassess.config import settings

MAX_CHARS = 2000  # same cap as the PDF chunker (bge-small window is 512 tokens)

_BANNER = re.compile(r"<!--.*?-->", re.S)
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_PARA = re.compile(r"^\d+\.\d+\s")  # numbered paragraph start, e.g. "4.2 "
_EFFECTIVE = re.compile(r"\|\s*Effective from\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|")


def _split_oversize(body: str) -> list[str]:
    """Split a long section at numbered-paragraph boundaries, packing greedily."""
    paras: list[str] = []
    for line in body.split("\n"):
        if _PARA.match(line) or not paras:
            paras.append(line)
        else:
            paras[-1] += "\n" + line
    parts, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) + 1 > MAX_CHARS:
            parts.append(cur)
            cur = p
        else:
            cur = f"{cur}\n{p}" if cur else p
    if cur:
        parts.append(cur)
    return parts


def chunk_policy(path: Path) -> list[dict]:
    """Return chunk records for one policy file, in the same shape as the DB columns."""
    doc_id = path.stem
    raw = path.read_text(encoding="utf-8")

    m = _EFFECTIVE.search(raw)
    effective_from = m.group(1) if m else None

    # The synthetic banner is dropped from chunk text. The disclosure lives in the
    # README; embedding it would make every chunk look alike to the retriever.
    raw = _BANNER.sub("", raw)

    title = None
    section = None  # heading of the current ## section
    sections: list[tuple[str, list[str]]] = []
    for line in raw.split("\n"):
        h = _HEADING.match(line)
        if h:
            level, text = len(h.group(1)), h.group(2)
            if level == 1:
                title = text
                section = None
            else:
                section = text
                sections.append((text, []))
            continue
        # Lines before the first ## (the header table) are metadata, not content.
        if section is not None:
            sections[-1][1].append(line)

    chunks: list[dict] = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        parts = _split_oversize(body) if len(body) > MAX_CHARS else [body]
        for part in parts:
            chunks.append(
                {
                    "chunk_id": f"{doc_id}:{len(chunks):04d}",
                    "corpus": "internal",
                    "doc_id": doc_id,
                    "clause_path": f"{title} > {heading}" if title else heading,
                    "text": part,
                    "status": "in_force",
                    "effective_from": effective_from,
                    "effective_to": None,
                    "document_type": "policy",
                    "amends": None,
                    "page_start": None,
                    "page_end": None,
                }
            )
    return chunks


def chunk_all_policies() -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(settings.internal_dir.glob("KST-*.md")):
        chunks.extend(chunk_policy(path))
    return chunks
