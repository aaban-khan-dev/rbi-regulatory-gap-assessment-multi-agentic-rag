"""Run the baseline gap-assessment graph on one circular.

    .\\.venv\\Scripts\\python.exe scripts\\run_assessment.py amd-ppi-2024-02
    .\\.venv\\Scripts\\python.exe scripts\\run_assessment.py path\\to\\circular.txt

The argument is a manifest doc_id (read from data/processed/<doc_id>.jsonl) or a
path to a plain-text file.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.config import settings  # noqa: E402
from regassess.graph import Register, build_graph  # noqa: E402


def load_circular(arg: str) -> tuple[str, str]:
    """Return (name, text). Chunk files are rendered with [clause X] markers so the
    extractor can cite real clause paths; a text file has no markers."""
    chunk_file = settings.processed_dir / f"{arg}.jsonl"
    if chunk_file.exists():
        chunks = [json.loads(line) for line in chunk_file.read_text(encoding="utf-8").splitlines()]
        parts = [
            f"[clause {c['clause_path']}] {c['text']}" if c["clause_path"] else c["text"]
            for c in chunks
        ]
        return arg, "\n\n".join(parts)
    path = Path(arg)
    if path.is_file():
        return path.stem, path.read_text(encoding="utf-8")
    sys.exit(f"error: '{arg}' is neither a chunked doc_id ({chunk_file}) nor a file path")


def _cut(text: str, width: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 3] + "..."


def print_table(register: Register) -> None:
    header = f"{'ID':<7} {'CLAUSE':<8} {'FORCE':<7} {'STATUS':<8} {'SEV':<7} {'CONTROLS':<28} RATIONALE"
    print(f"\nGap register: {register.source}  (model {register.model})")
    print(header)
    print("-" * len(header))
    for f in register.findings:
        controls = _cut(", ".join(f.control_doc_ids), 28)
        print(
            f"{f.obligation_id:<7} {str(f.regulation_clause_path):<8} {f.normative_force:<7} "
            f"{f.status:<8} {f.severity:<7} {controls:<28} {_cut(f.rationale, 70)}"
        )
    print(f"\nStatus counts: {register.status_counts}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("circular", help="manifest doc_id or path to a text file")
    args = parser.parse_args()

    name, text = load_circular(args.circular)
    result = build_graph().invoke({"circular_text": text, "source_name": name})
    register: Register = result["register"]

    out = settings.output_dir / f"{name}_register.json"
    out.write_text(register.model_dump_json(indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    print_table(register)


if __name__ == "__main__":
    main()
