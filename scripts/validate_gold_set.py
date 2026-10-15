"""Check data/eval/gold_set.yaml against the chunks actually loaded in Postgres.

    .\\.venv\\Scripts\\python.exe scripts\\validate_gold_set.py

Run after every build_index.py: chunk ids are positional, so a re-chunk can
silently move a gold answer, and a manifest date change can take one out of
force. Exit code 1 if any check fails.
"""

import sys
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.config import settings  # noqa: E402
from regassess.db import get_connection  # noqa: E402

GOLD_PATH = settings.data_dir / "eval" / "gold_set.yaml"
GROUND_TRUTH_PATH = settings.internal_dir / "gap_ground_truth.yaml"


def load_chunks(chunk_ids: set[str]) -> dict[str, dict]:
    """Fetch only the chunks the gold set refers to, keyed by chunk_id."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT chunk_id, clause_path, corpus, effective_from, effective_to "
            "FROM chunks WHERE chunk_id = ANY(%s)",
            (sorted(chunk_ids),),
        ).fetchall()
    return {
        cid: {"clause_path": path, "corpus": corpus, "from": start, "to": end}
        for cid, path, corpus, start, end in rows
    }


def status_problems(today: date) -> list[str]:
    """Every regulation document's status must agree with its effective_to on today's
    date: in_force exactly when effective_to is null or still ahead."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT doc_id, status, effective_to FROM chunks WHERE corpus = 'regulation' ORDER BY doc_id"
        ).fetchall()
    problems = []
    for doc_id, status, end in rows:
        current = end is None or today < end
        if (status == "in_force") != current:
            problems.append(f"{doc_id}: status {status}, effective_to {end}, today {today}")
    return problems


def in_force(chunk: dict, as_of: date) -> bool:
    """The window rule in docs/EVALUATION.md: from <= as_of < to, a null end is open."""
    return (chunk["from"] is None or chunk["from"] <= as_of) and (chunk["to"] is None or as_of < chunk["to"])


def ground_truth_dates() -> dict[str, str]:
    """Obligation id -> the date it is assessed on (row as_of, else the meta default)."""
    gt = yaml.safe_load(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    default = gt["meta"]["assessment_as_of"]
    return {o["id"]: o.get("as_of", default) for o in gt["obligations"]}


def main() -> int:
    items = yaml.safe_load(GOLD_PATH.read_text(encoding="utf-8"))["items"]
    referenced = {cid for it in items for cid in it.get("gold_chunk_ids", []) + it.get("stale_chunk_ids", [])}
    db = load_chunks(referenced)

    # One list of failure messages per check, so the report shows every problem at once.
    checks: dict[str, list[str]] = {
        "every item has at least one gold chunk": [],
        "every gold_chunk_id exists in Postgres": [],
        "every gold_clause_path matches the chunk's clause_path": [],
        "no duplicate queries (query + as_of)": [],
        "item_ids are unique": [],
        "corpus field matches each gold chunk's corpus": [],
        "every stale_chunk_id exists in Postgres": [],
        "regulation items have as_of, internal items do not": [],
        "every gold chunk is in force on the item's as_of": [],
        "no stale chunk is in force on the item's as_of": [],
        "as_of matches the obligation's date in gap_ground_truth.yaml": [],
        "document status agrees with effective_to (today)": status_problems(date.today()),
    }
    obligation_dates = ground_truth_dates()

    for item_id, n in Counter(it["item_id"] for it in items).items():
        if n > 1:
            checks["item_ids are unique"].append(f"{item_id} appears {n} times")

    # The version pairs ask the same question at two dates on purpose, so the
    # date is part of the key. Case and spacing are normalised.
    seen: dict[tuple, str] = {}
    for it in items:
        key = (" ".join(it["query"].lower().split()), it.get("as_of"))
        if key in seen:
            checks["no duplicate queries (query + as_of)"].append(f"{it['item_id']} repeats {seen[key]}")
        seen.setdefault(key, it["item_id"])

    for it in items:
        iid = it["item_id"]
        gold, paths = it.get("gold_chunk_ids") or [], it.get("gold_clause_paths") or []
        if not gold:
            checks["every item has at least one gold chunk"].append(iid)
        if len(gold) != len(paths):
            checks["every gold_clause_path matches the chunk's clause_path"].append(
                f"{iid}: {len(gold)} chunk ids but {len(paths)} clause paths"
            )
        for cid, expected in zip(gold, paths):
            chunk = db.get(cid)
            if chunk is None:
                checks["every gold_chunk_id exists in Postgres"].append(f"{iid}: {cid}")
                continue
            if chunk["clause_path"] != expected:
                checks["every gold_clause_path matches the chunk's clause_path"].append(
                    f"{iid}: {cid} is {chunk['clause_path']!r}, gold set says {expected!r}"
                )
            if chunk["corpus"] != it["corpus"]:
                checks["corpus field matches each gold chunk's corpus"].append(
                    f"{iid}: {cid} is in {chunk['corpus']}, item says {it['corpus']}"
                )
        for cid in it.get("stale_chunk_ids", []):
            if cid not in db:
                checks["every stale_chunk_id exists in Postgres"].append(f"{iid}: {cid}")

        raw_as_of = it.get("as_of")
        if (it["corpus"] == "regulation") != (raw_as_of is not None):
            checks["regulation items have as_of, internal items do not"].append(
                f"{iid}: corpus {it['corpus']}, as_of {raw_as_of}"
            )
        if raw_as_of is None:
            continue
        if it["source"].startswith("OBL-") and obligation_dates.get(it["source"]) != raw_as_of:
            checks["as_of matches the obligation's date in gap_ground_truth.yaml"].append(
                f"{iid}: {raw_as_of}, {it['source']} is {obligation_dates.get(it['source'])}"
            )
        as_of = date.fromisoformat(raw_as_of)
        for cid in gold:
            if cid in db and not in_force(db[cid], as_of):
                c = db[cid]
                checks["every gold chunk is in force on the item's as_of"].append(
                    f"{iid}: {cid} valid {c['from']} to {c['to']}, as_of {as_of}"
                )
        for cid in it.get("stale_chunk_ids", []):
            if cid in db and in_force(db[cid], as_of):
                c = db[cid]
                checks["no stale chunk is in force on the item's as_of"].append(
                    f"{iid}: {cid} valid {c['from']} to {c['to']}, as_of {as_of}"
                )

    failed = 0
    for name, problems in checks.items():
        print(f"[{'FAIL' if problems else 'PASS'}] {name}")
        for p in problems:
            print(f"         {p}")
        failed += bool(problems)

    print(f"\n{len(items)} items, {len(referenced)} distinct chunks referenced, {len(db)} found in Postgres")
    for field in ("category", "corpus"):
        counts = Counter(it[field] for it in items)
        print(f"by {field}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"\n{failed} check(s) failed" if failed else "\nall checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
