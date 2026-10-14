"""Check that synthetic policies do not reuse the regulation's wording.

1. Phrase reuse: for every policy file in data/internal/, find each run of
   MIN_SPAN or more consecutive words that also appears in any RBI chunk in
   data/processed/. Runs made only of statute or list names (ALLOWED_NAMES)
   are ignored, because those cannot be paraphrased.
2. For each ground-truth row, the longest run the policy shares with that
   row's own chunk.
3. Keyword overlap, COVERED rows only: the chunk's distinctive words compared
   against the single policy named in policy_doc. Distinctive words are
   lowercase alphabetic words of 3+ letters, minus English stopwords, with a
   crude plural fold. Numbers are excluded: a policy covering a limit has to
   state the same figure. Two scores:
     plain  share of the chunk's distinctive words found in the policy
     idf    the same share weighted by inverse document frequency over all RBI
            chunks, so rare words count more (closer to what BM25 rewards)

Exit code 1 if any policy has a non-allowed shared run of MIN_SPAN words, or
if either keyword-overlap median exceeds MAX_MEDIAN_OVERLAP.
"""

import json
import math
import re
import statistics
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from regassess.config import settings  # noqa: E402

MIN_SPAN = 5
MAX_MEDIAN_OVERLAP = 0.4

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each either etc few for from further had has
have having he her here hers herself him himself his how however i if in into is it its itself just me
more most my myself no nor not now of off on once only or other our ours ourselves out over own same she
should so some such than that the their theirs them themselves then there these they this those through
to too under until up upon very via was we were what when where which while who whom why will with would
you your yours yourself yourselves shall may must per inter alia viz
""".split())
WORD = re.compile(r"[a-z]+")

# Proper names a policy has to quote verbatim. A shared run is allowed only if
# it lies entirely inside one of these.
ALLOWED_NAMES = [
    "ministry of home affairs",
    "prevention and suppression of terrorism order 2007",
    "weapons of mass destruction act 2005",
    "section 12a of the weapons of mass destruction act 2005",
    "prevention of money laundering act",
    "isil da esh and al qaida sanctions list",
    "un security council isil da esh and al qaida sanctions list",
]

TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def load_chunks() -> dict[str, dict]:
    chunks = {}
    for path in sorted(settings.processed_dir.glob("*.jsonl")):
        for line in path.open(encoding="utf-8"):
            record = json.loads(line)
            chunks[record["chunk_id"]] = record
    return chunks


def shared_spans(policy: list[str], reg_ngrams: set[tuple]) -> list[tuple[int, int]]:
    """Maximal runs in `policy` whose every MIN_SPAN-gram occurs in the regulation."""
    hits = [
        i for i in range(len(policy) - MIN_SPAN + 1)
        if tuple(policy[i:i + MIN_SPAN]) in reg_ngrams
    ]
    spans = []
    for i in hits:
        if spans and i <= spans[-1][1] - MIN_SPAN + 1:
            spans[-1] = (spans[-1][0], i + MIN_SPAN)
        else:
            spans.append((i, i + MIN_SPAN))
    return spans


def is_allowed(span_words: list[str]) -> bool:
    text = " ".join(span_words)
    return any(text in name for name in ALLOWED_NAMES)


def longest_common_run(a: list[str], b: list[str]) -> list[str]:
    best_len, best_end = 0, 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best_len:
                    best_len, best_end = cur[j], i
        prev = cur
    return a[best_end - best_len:best_end]


def content_words(text: str) -> set[str]:
    words = set()
    for w in WORD.findall(text.lower()):
        if len(w) < 3 or w in STOPWORDS:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        words.add(w)
    return words


def keyword_overlap(truth: dict, chunks: dict, policy_texts: dict) -> tuple[float, float]:
    """Print per-row overlap for COVERED rows; return (median plain, median idf)."""
    df: dict[str, int] = {}
    for chunk in chunks.values():
        for w in content_words(chunk["text"]):
            df[w] = df.get(w, 0) + 1
    n = len(chunks)
    idf = {w: math.log(n / c) for w, c in df.items()}

    rows = []
    for row in truth["obligations"]:
        if row["outcome"] != "COVERED":
            continue
        reg = content_words(chunks[row["chunk_id"]]["text"])
        pol = content_words(policy_texts[row["policy_doc"]])
        shared = reg & pol
        plain = len(shared) / len(reg)
        weighted = sum(idf[w] for w in shared) / sum(idf[w] for w in reg)
        top = sorted(shared, key=lambda w: -idf[w])[:6]
        rows.append((plain, weighted, row, top))

    print("\nKeyword overlap, COVERED rows: chunk's distinctive words vs its own policy_doc")
    print(f"  {'row':7}{'clause':<20}{'policy':<13}{'plain':>6}{'idf':>6}  rarest shared words")
    for plain, weighted, row, top in sorted(rows, key=lambda r: -r[0]):
        clause = f"{row['doc_id'][3:6]} {row['clause_path']}"
        print(f"  {row['id']:7}{clause:<20}{row['policy_doc']:<13}{plain:6.2f}{weighted:6.2f}  {', '.join(top)}")
    med_plain = statistics.median(r[0] for r in rows)
    med_idf = statistics.median(r[1] for r in rows)
    print(f"  median plain {med_plain:.2f}, median idf {med_idf:.2f} (limit {MAX_MEDIAN_OVERLAP})")
    print("  worst five by plain:", ", ".join(f"{r[2]['id']} {r[0]:.2f}" for r in sorted(rows, key=lambda r: -r[0])[:5]))
    print("  worst five by idf:  ", ", ".join(f"{r[2]['id']} {r[1]:.2f}" for r in sorted(rows, key=lambda r: -r[1])[:5]))
    return med_plain, med_idf


def main() -> int:
    chunks = load_chunks()
    reg_ngrams = set()
    for chunk in chunks.values():
        t = tokens(chunk["text"])
        reg_ngrams.update(tuple(t[i:i + MIN_SPAN]) for i in range(len(t) - MIN_SPAN + 1))

    policy_texts = {p.stem: p.read_text(encoding="utf-8")
                    for p in sorted(settings.internal_dir.glob("*.md"))}
    policies = {name: tokens(text) for name, text in policy_texts.items()}

    print(f"Shared runs of {MIN_SPAN}+ words between each policy and the whole RBI corpus")
    failures = 0
    for name, toks in policies.items():
        spans = shared_spans(toks, reg_ngrams)
        bad = [toks[s:e] for s, e in spans if not is_allowed(toks[s:e])]
        allowed = len(spans) - len(bad)
        status = "FAIL" if bad else "ok"
        print(f"  {status:4} {name}: {len(bad)} flagged, {allowed} allowed names")
        for words in bad:
            print(f"         -> {' '.join(words)}")
        failures += len(bad)

    truth = yaml.safe_load((settings.internal_dir / "gap_ground_truth.yaml").read_text(encoding="utf-8"))
    print("\nLongest run each policy shares with its own clause's chunk")
    for row in truth["obligations"]:
        run = longest_common_run(policies[row["policy_doc"]], tokens(chunks[row["chunk_id"]]["text"]))
        print(f"  {row['id']} {row['outcome']:8} {row['doc_id']} {row['clause_path']:<11} "
              f"{row['policy_doc']}: {len(run)} words  '{' '.join(run)}'")

    med_plain, med_idf = keyword_overlap(truth, chunks, policy_texts)

    print(f"\n{failures} flagged run(s) across {len(policies)} policies")
    too_high = max(med_plain, med_idf) > MAX_MEDIAN_OVERLAP
    if too_high:
        print(f"Keyword-overlap median above {MAX_MEDIAN_OVERLAP}")
    return 1 if failures or too_high else 0


if __name__ == "__main__":
    sys.exit(main())
