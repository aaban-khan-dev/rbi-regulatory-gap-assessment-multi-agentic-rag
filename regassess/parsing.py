"""PDF parsing: a thin wrapper around Docling.

Deliberately contains no chunking logic. It turns a PDF into Docling's
structured documents and nothing more.

Long PDFs are parsed in page-range segments so one run can stop and resume
(Docling on CPU is ~10s/page). Segments are cached separately. Page numbers
stay absolute across segments, and `iter_items` yields one continuous stream.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pypdfium2
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DoclingDocument

from regassess.config import settings

CACHE_DIR = settings.processed_dir / "_docling_cache"
SEGMENT_PAGES = 25  # ~4 minutes per segment on CPU
SINGLE_SEGMENT_MAX = 40  # documents up to this many pages are parsed in one go


class ParseIncomplete(Exception):
    """Raised when the new-segment budget ran out before the document finished."""

    def __init__(self, done: int, total: int):
        super().__init__(f"{done}/{total} segments parsed")
        self.done, self.total = done, total


@lru_cache(maxsize=1)
def _converter() -> DocumentConverter:
    # Building the converter loads layout/table models; do it once per process.
    # OCR is off: these PDFs have a text layer. Measured on md-ppi-2021: OCR on
    # and off give identical items, and OCR off is ~35% faster.
    options = PdfPipelineOptions(do_ocr=False)
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def page_count(path: Path) -> int:
    pdf = pypdfium2.PdfDocument(str(path))
    try:
        return len(pdf)
    finally:
        pdf.close()


def segments(pages: int) -> list[tuple[int, int]]:
    """1-based inclusive page ranges to parse."""
    if pages <= SINGLE_SEGMENT_MAX:
        return [(1, pages)]
    return [(s, min(s + SEGMENT_PAGES - 1, pages)) for s in range(1, pages + 1, SEGMENT_PAGES)]


def _cache_path(sha256: str, start: int, end: int) -> Path:
    # The hash comes from the manifest, so a changed PDF can never hit a stale
    # entry. "noocr" is in the name so flipping the OCR setting cannot silently
    # reuse these files.
    return CACHE_DIR / f"{sha256}.noocr.p{start}-{end}.json"


def parse_pdf(
    path: Path, sha256: str, max_new_segments: int | None = None
) -> list[DoclingDocument]:
    """Parse a PDF into one DoclingDocument per segment, using the cache.

    At most `max_new_segments` uncached segments are parsed per call (None =
    no limit); if more remain, ParseIncomplete is raised and a re-run resumes.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    plan = segments(page_count(path))
    documents: list[DoclingDocument] = []
    parsed_now = 0
    for index, (start, end) in enumerate(plan):
        cached = _cache_path(sha256, start, end)
        if cached.exists():
            documents.append(DoclingDocument.load_from_json(cached))
            continue
        if max_new_segments is not None and parsed_now >= max_new_segments:
            raise ParseIncomplete(index, len(plan))
        document = _converter().convert(str(path), page_range=(start, end)).document
        document.save_as_json(cached)
        documents.append(document)
        parsed_now += 1
    return documents


def iter_items(documents: list[DoclingDocument]) -> Iterator[tuple]:
    """One continuous stream of (item, owning document) across all segments."""
    for document in documents:
        for item, _level in document.iterate_items():
            yield item, document


# --- Watermark ---------------------------------------------------------------
# Withdrawn documents carry a red diagonal "Withdrawn" stamp, roughly one per
# page. Docling extracts it as ordinary text: sometimes its own item, usually
# merged into a paragraph (even mid-sentence, or glued to a word with no space).
# Case-sensitive on purpose: legitimate prose says "withdrawn" in lowercase.
_WATERMARK = re.compile(r"\s*Withdrawn(?![a-z])")
_CONTEXT = 35  # characters of surrounding text kept per hit, for human review


@dataclass
class WatermarkReport:
    count: int = 0
    pages: set[int] = field(default_factory=set)
    contexts: list[str] = field(default_factory=list)

    @property
    def detected(self) -> bool:
        return self.count > 0


def _strip(text: str, page: int | None, report: WatermarkReport) -> str:
    def remove(match: re.Match) -> str:
        report.count += 1
        if page is not None:
            report.pages.add(page)
        start, end = match.start(), match.end()
        before = text[max(0, start - _CONTEXT) : start]
        after = text[end : end + _CONTEXT]
        report.contexts.append(f"p{page}: ...{before}[WATERMARK]{after}...")
        return ""

    return _WATERMARK.sub(remove, text)


def strip_watermark(documents: list[DoclingDocument]) -> WatermarkReport:
    """Remove the watermark from every text item and table cell, in memory only.

    The on-disk parse cache is left untouched, so the raw parse stays
    reproducible. Items that become empty are dropped later by the chunker.
    """
    report = WatermarkReport()
    for item, _document in iter_items(documents):
        page = item.prov[0].page_no if getattr(item, "prov", None) else None
        for attribute in ("text", "orig"):
            value = getattr(item, attribute, None)
            if value:
                # "orig" mirrors "text", so only count hits from "text".
                scratch = report if attribute == "text" else WatermarkReport()
                setattr(item, attribute, _strip(value, page, scratch))
        data = getattr(item, "data", None)
        for cell in getattr(data, "table_cells", None) or []:
            cell.text = _strip(cell.text, page, report)
    return report
