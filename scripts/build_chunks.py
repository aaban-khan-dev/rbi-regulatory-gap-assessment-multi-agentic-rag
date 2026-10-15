"""Parse and chunk the RBI corpus: data/raw/*.pdf -> data/processed/<doc_id>.jsonl.

Usage:
    .\\.venv\\Scripts\\python.exe scripts\\build_chunks.py
    .\\.venv\\Scripts\\python.exe scripts\\build_chunks.py --doc md-ppi-2021
    .\\.venv\\Scripts\\python.exe scripts\\build_chunks.py --max-new-segments 2

Docling on CPU is slow (~10s/page), so long PDFs are parsed in segments and
cached. --max-new-segments stops after N new segments so a run fits inside a
time limit; re-run to resume. Cached segments are free.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.chunking import chunk_document  # noqa: E402
from regassess.config import settings  # noqa: E402
from regassess.parsing import ParseIncomplete, page_count, parse_pdf, strip_watermark  # noqa: E402

MANIFEST = settings.data_dir / "corpus_manifest.yaml"
REPORT = settings.processed_dir / "_build_report.json"


def process(entry: dict, max_new_segments: int | None) -> dict | None:
    doc_id = entry["doc_id"]
    pdf = settings.raw_dir / f"{doc_id}.pdf"
    try:
        documents = parse_pdf(pdf, entry["sha256"], max_new_segments)
    except ParseIncomplete as stopped:
        print(f"  {doc_id}: parse incomplete ({stopped}); re-run to continue", flush=True)
        return None

    watermark = strip_watermark(documents)
    result = chunk_document(doc_id, documents, entry)
    out = settings.processed_dir / f"{doc_id}.jsonl"
    with out.open("w", encoding="utf-8") as handle:
        for chunk in result.chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    stats = result.stats
    return {
        "doc_id": doc_id,
        "manifest_status": entry["status"],
        "pages": page_count(pdf),
        "chunks": len(result.chunks),
        "null_clause_path": result.null_path_count,
        "median_chars": result.median_chars,
        "depth": result.depth_distribution(),
        "clause_depth": result.clause_depth_distribution(),
        "stats": vars(stats),
        "watermark_detected": watermark.detected,
        "watermark_count": watermark.count,
        "watermark_pages": sorted(watermark.pages),
        "watermark_contexts": watermark.contexts,
    }


def print_tables(rows: list[dict]) -> None:
    print("\nSUMMARY")
    print(f"{'doc_id':<18}{'pages':>6}{'chunks':>8}{'null path':>14}{'median chars':>14}")
    for r in rows:
        share = f"{r['null_clause_path']} ({100 * r['null_clause_path'] / max(r['chunks'], 1):.0f}%)"
        print(f"{r['doc_id']:<18}{r['pages']:>6}{r['chunks']:>8}{share:>14}{r['median_chars']:>14.0f}")

    print("\nCLAUSE_PATH DEPTH: by chunk (first clause) | by every clause inside chunks")
    print(f"{'doc_id':<18}{'1-lvl':>6}{'2-lvl':>6}{'3+lvl':>6}   |{'1-lvl':>6}{'2-lvl':>6}{'3+lvl':>6}")
    for r in rows:
        d, c = r["depth"], r["clause_depth"]
        print(f"{r['doc_id']:<18}{d['1']:>6}{d['2']:>6}{d['3+']:>6}   |{c['1']:>6}{c['2']:>6}{c['3+']:>6}")

    print("\nCLEANUP DIAGNOSTICS")
    print(
        f"{'doc_id':<18}{'pg-brk merges':>14}{'same-pg merges':>15}{'footnotes cut':>14}{'empty cut':>10}"
        f"{'unplaced':>9}{'oversize':>9}{'unterminated':>13}"
    )
    for r in rows:
        s = r["stats"]
        print(
            f"{r['doc_id']:<18}{s['page_break_merges']:>14}{s['same_page_merges']:>15}"
            f"{s['footnote_items_dropped']:>14}{s['empty_items_dropped']:>10}{s['unplaced_numbers']:>9}"
            f"{s['oversize_chunks']:>9}{s['unterminated_chunks']:>13}"
        )

    print("\nPARENT-HEADING CONTEXT (chunks that gained a context line)")
    total_ctx = total_chunks = 0
    for r in rows:
        n = r["stats"].get("context_added", 0)
        total_ctx, total_chunks = total_ctx + n, total_chunks + r["chunks"]
        print(f"{r['doc_id']:<18}{n:>6} of {r['chunks']}")
    print(f"{'total':<18}{total_ctx:>6} of {total_chunks}")

    print("\nWATERMARK CENSUS vs MANIFEST STATUS")
    print(f"{'doc_id':<18}{'manifest status':<17}{'detected':>9}{'count':>7}{'pages hit':>11}  verdict")
    disagreements = 0
    for r in rows:
        # A document that is not in force is expected to carry the Withdrawn stamp.
        expected = r["manifest_status"] != "in_force"
        agrees = r["watermark_detected"] == expected
        disagreements += not agrees
        verdict = "ok" if agrees else (
            "DISAGREES: stamped Withdrawn but manifest says in_force"
            if r["watermark_detected"]
            else "DISAGREES: manifest says not in force but no stamp found"
        )
        pages_hit = f"{len(r['watermark_pages'])}/{r['pages']}"
        print(
            f"{r['doc_id']:<18}{r['manifest_status']:<17}{str(r['watermark_detected']):>9}"
            f"{r['watermark_count']:>7}{pages_hit:>11}  {verdict}"
        )
    print(f"\n{disagreements} document(s) where watermark and manifest status disagree.")
    print(f"Watermark hits with surrounding text, per document: {REPORT}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--doc", action="append", help="doc_id to process (repeatable); default all")
    parser.add_argument("--max-new-segments", type=int, default=None)
    args = parser.parse_args()

    entries = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))["documents"]
    if args.doc:
        entries = [e for e in entries if e["doc_id"] in args.doc]

    report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
    incomplete = False
    for entry in entries:
        print(f"{entry['doc_id']} ...", flush=True)
        row = process(entry, args.max_new_segments)
        if row is None:
            incomplete = True
        else:
            report[entry["doc_id"]] = row
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    order = [e["doc_id"] for e in yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))["documents"]]
    print_tables([report[d] for d in order if d in report])
    return 2 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
