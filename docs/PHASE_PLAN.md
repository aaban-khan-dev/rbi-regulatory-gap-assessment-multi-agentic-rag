# Phase plan

17 phases in five stages. Front-loaded: a demoable baseline by Phase 5, first
measured numbers by Phase 7.

## Stage A — Data foundation

- **0. Repo and environment** — venv, config module, setup verification.
  *Exit: `check_setup.py` passes both checks.*
- **1. RBI corpus acquisition** — Master Directions plus amendment circulars;
  manifest with doc_id, title, issue date, effective_from, "as amended up to",
  source URL, SHA-256.
  *Exit: PDFs on disk, manifest complete. The manifest is what makes Phase 10
  possible — without it there is nothing to filter on.*
- **2. Parsing and structure-aware chunking** — Docling parse, clause-hierarchy
  walk, chunks carrying `clause_path`.
  *Exit: `data/processed/rbi_chunks.jsonl`, 20 chunks spot-checked against the
  source PDFs. Bad chunk boundaries cap every downstream metric.*
- **3. Synthetic internal policy corpus** — design the planted coverage
  patterns first, then write 15-25 policy documents to them. Parse through the
  Phase 2 pipeline.
  *Exit: internal corpus parsed, planted gaps documented. If the policies match
  the regulation cleanly, gap-classification accuracy is meaningless.*

## Stage B — First working system

- **4. Vector store and naive retrieval** — Postgres + pgvector in Docker,
  schema for documents / chunks / embeddings, bge-small embeddings, naive top-k
  cosine, CLI query.
  *Exit: a question returns plausible clauses.*
- **5. Naive end-to-end baseline** — minimal LangGraph: retrieve regulation →
  crude obligation extraction → retrieve controls → gap analyst → write
  register. No reranking, no versioning, no verification. Deliberately dumb.
  *Exit: a gap register generated from a real circular. First demoable
  artifact and the baseline row of the ablation table.*

## Stage C — Measurement

- **6. Gold set** — 80-100 LLM-drafted and human-reviewed items: retrieval questions with
  ground-truth clause IDs, obligation-extraction cases with expected fields,
  gap-classification cases with expected verdicts. Labelling helper script.
  *Exit: gold set (YAML) committed. Slow and tedious; non-negotiable.*
- **7. Evaluation harness** — one script, one config flag, runs any retrieval
  configuration against the gold set; recall@10, MRR, nDCG. LLM response
  caching so re-runs don't burn free-tier quota.
  *Exit: baseline numbers for Phase 5. From here every change is measured.*

## Stage D — Making it good

- **8. Hybrid retrieval** — Postgres full-text/BM25 alongside vector search,
  RRF fusion. *Exit: ablation row 2.*
- **9. Cross-encoder reranking** — local bge-reranker over fused candidates.
  *Exit: ablation row 3.*
- **10. Contextual retrieval and version awareness** — LLM-generated chunk
  context headers, `effective_from`/`effective_to`, as-of-date filtering,
  supersession handling.
  *Exit: ablation row 4 plus stale-version-retrieval-rate, which should drop
  sharply. This is the row that proves the domain thinking.*
- **11. Structured obligation extraction** — Pydantic schema: obligation ID,
  normative force, applicable entity, deadline, source clause path.
  *Exit: measured against the gold extraction cases.*
- **12. Gap analyst and register writer** — covered / partial / gap / unclear,
  with severity, rationale and owner; plus the impact memo.
  *Exit: measured gap-classification accuracy.*
- **13. Verifier and abstention** — every claim mapped to a retrieved span with
  doc ID and version hash; unsupported claims bounce to the writer or escalate
  to human review.
  *Exit: measured faithfulness and citation accuracy.*

## Stage E — Production polish

- **14. Reliability and observability** — retries with backoff, timeouts, token
  and cost accounting per run, structured tracing, LangGraph checkpointing,
  pytest over chunking, retrieval and schema validation.
- **15. API, queue and demo UI** — port the FastAPI submit-and-poll and Celery
  task from `swarm-reference/` (rewritten to this project's state object and
  node names), minimal Streamlit demo, full `docker-compose up`.
- **16. Ablation table, bake-off, README, rehearsal** — the complete ablation
  table across all four configurations and every metric; a small model bake-off
  on ~20 gold questions; stack-choices-and-tradeoffs section; synthesis
  disclosure; demo script; interview rehearsal.

## Out of scope

GraphRAG, ColPali or visual retrieval, fine-tuned embeddings, multimodal input,
any UI beyond a minimal Streamlit or FastAPI demo — unless measurement
justifies it. A smaller system I can defend beats a larger one I cannot.
