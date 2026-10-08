# Project brief

## Problem

A payments company receives a new RBI circular. Compliance staff must read it,
identify new or changed obligations, check each against the company's internal
policies and SOPs, and produce a gap register: what is covered, partially
covered, or a genuine gap, with severity and owner. This is days of senior
analyst time per circular, and a missed clause is a regulatory exposure nobody
knows about.

It is also a moving target. Circulars amend earlier Master Directions, so what
a rule says depends on the date you ask about.

## What we are building

A document-triggered agentic RAG system. Input: a circular. Output: a gap
register and impact memo where every finding is traced to a specific clause in
a specific version of a specific document.

Document-triggered, not query-triggered: there is no user query to embed, so
retrieval queries are generated from the extracted obligations.

## Agent graph

1. **Regulation retriever** — hybrid search over the RBI corpus, version-aware
   with an as-of-date filter
2. **Obligation extractor** — structured output: obligation ID, normative force
   (shall / should / may), applicable entity, deadline, source clause path
3. **Control retriever** — candidate matching controls from the internal policy
   corpus, per obligation
4. **Gap analyst** — compares obligation against control, classifies as
   covered / partial / gap / unclear, with severity and rationale
5. **Register writer** — produces the gap register and impact memo
6. **Verifier** — claim-level citation check; every assertion must map to a
   retrieved span with document ID and version hash. Unsupported claims return
   to the writer or escalate for human review.

## Retrieval stack

Docling parsing, structure-aware chunking preserving clause paths, metadata
(`doc_id`, `version`, `effective_from`, `effective_to`, `clause_path`,
`obligation_type`, `jurisdiction`), pgvector plus BM25, RRF fusion,
cross-encoder reranking, contextual retrieval. Abstention: low-confidence
findings route to "needs human review".

## Corpora

**External (real):** RBI Master Directions on Prepaid Payment Instruments, KYC,
and Digital Payment Security Controls, plus amendment circulars. These carry
"as amended up to" dates, so supersession is native to the data.

**Internal (synthetic):** 15-25 generated policy documents for a fictional
payments company — KYC SOP, customer onboarding, transaction limits, data
retention, grievance redressal, agent network policy. The synthetic corpus is
designed with deliberately planted patterns: some obligations fully covered,
some partial, some absent, some covered only by a stale policy version.
Synthesis is disclosed plainly in the README.

## Measurement layer — the core differentiator

Hand-labelled gold set of 80-100 items with ground-truth clause IDs.

- Retrieval: recall@10, MRR, nDCG
- Generation: faithfulness, citation accuracy
- Domain-specific: stale-version retrieval rate, gap-classification accuracy

**Headline deliverable:** an ablation table across naive → hybrid → reranked →
version-aware configurations, showing every metric at each step. This is what
makes the project defensible when an interviewer asks how I know it works.

## Why this project

It matches the target job description (policy, regulated and compliance
documents), builds on digital financial services domain knowledge I already
have, produces a consulting-style deliverable rather than a chatbot, and forces
the hard retrieval problems — versioning, supersession, clause-level citation,
cross-corpus comparison — instead of letting top-k plus a prompt suffice.
