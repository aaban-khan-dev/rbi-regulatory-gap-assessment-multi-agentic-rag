"""Naive end-to-end baseline: circular in, gap register out.

Four nodes in a straight line, no branching, no verification:
extract_obligations -> retrieve_controls -> assess_gaps -> write_register
"""

from datetime import datetime, timezone
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from regassess.config import settings
from regassess.llm import generate_structured
from regassess.retrieval import search

# Controls retrieved per obligation. A constant, not a setting: the ablation in
# Phase 7+ changes the retriever, not this number.
TOP_K_CONTROLS = 5


# --- Pydantic models -------------------------------------------------------------
# These double as the Gemini response schemas, so the shape is enforced by the API
# and re-validated on our side.


class ExtractedObligation(BaseModel):
    """What the LLM returns for one obligation. No ID: code assigns that."""

    text: str = Field(description="The obligation, restated as one self-contained sentence.")
    normative_force: Literal["shall", "should", "may"]
    clause_path: str | None = Field(
        description="The clause number from the [clause X] marker the obligation came from; null if none."
    )


class ExtractedObligations(BaseModel):
    obligations: list[ExtractedObligation]


class Obligation(ExtractedObligation):
    obligation_id: str


class Assessment(BaseModel):
    status: Literal["covered", "partial", "gap", "unclear"]
    severity: Literal["high", "medium", "low", "none"]
    rationale: str = Field(description="One sentence explaining the verdict.")


class Finding(BaseModel):
    """One row of the register: the obligation, the verdict, and where both came from."""

    obligation_id: str
    obligation_text: str
    normative_force: str
    regulation_doc_id: str
    regulation_clause_path: str | None
    status: str
    severity: str
    rationale: str
    control_doc_ids: list[str]
    control_chunk_ids: list[str]


class Register(BaseModel):
    source: str
    model: str
    top_k_controls: int
    generated_at: str
    status_counts: dict[str, int]
    findings: list[Finding]


# --- State ------------------------------------------------------------------------


class State(TypedDict, total=False):
    circular_text: str  # input
    source_name: str  # input: the doc_id or file stem, used in the register
    obligations: list[Obligation]
    controls: dict[str, list[dict]]  # obligation_id -> retrieved chunks, best first
    assessments: dict[str, Assessment]  # obligation_id -> verdict
    register: Register


# --- Nodes ------------------------------------------------------------------------


def extract_obligations(state: State) -> dict:
    """One Gemini call over the whole circular -> list of obligations."""
    prompt = (
        "You are a compliance analyst. Read the RBI circular below and list every "
        "obligation it places on regulated entities (payment system operators and "
        "PPI issuers). Include only requirements, not background or recitals.\n"
        "For each: restate it as one self-contained sentence; set normative_force to "
        "'shall' for mandatory, 'should' for recommended, 'may' for permitted; and "
        "set clause_path to the number in the [clause X] marker it came from "
        "(null if the text has no markers).\n\n"
        f"CIRCULAR:\n{state['circular_text']}"
    )
    extracted = generate_structured(prompt, ExtractedObligations)
    # IDs come from code, not the model, so they are stable and cannot collide.
    obligations = [
        Obligation(obligation_id=f"OBL-{i:02d}", **o.model_dump())
        for i, o in enumerate(extracted.obligations, 1)
    ]
    print(f"extract_obligations: {len(obligations)} obligations")
    return {"obligations": obligations}


def retrieve_controls(state: State) -> dict:
    """Naive vector search of the internal corpus, query = the obligation text."""
    controls = {
        o.obligation_id: search(o.text, k=TOP_K_CONTROLS, corpus="internal")
        for o in state["obligations"]
    }
    print(f"retrieve_controls: top-{TOP_K_CONTROLS} for {len(controls)} obligations")
    return {"controls": controls}


def _format_controls(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{c['doc_id']} | {c['clause_path']}]\n{c['text']}" for c in chunks
    )


def assess_gaps(state: State) -> dict:
    """One Gemini call per obligation, judged only against its retrieved controls."""
    assessments = {}
    for o in state["obligations"]:
        prompt = (
            "You are a compliance analyst comparing a regulatory obligation to a "
            "company's internal policy excerpts. Judge ONLY from the excerpts shown.\n"
            "status: 'covered' = excerpts fully satisfy the obligation; 'partial' = "
            "some but not all of it; 'gap' = no excerpt addresses it; 'unclear' = "
            "excerpts are related but you cannot tell.\n"
            "severity: the regulatory exposure if this is not met - high, medium or "
            "low; 'none' when covered.\n"
            "rationale: one sentence.\n\n"
            f"OBLIGATION ({o.normative_force}): {o.text}\n\n"
            f"INTERNAL POLICY EXCERPTS:\n{_format_controls(state['controls'][o.obligation_id])}"
        )
        assessments[o.obligation_id] = generate_structured(prompt, Assessment)
        print(f"assess_gaps: {o.obligation_id} -> {assessments[o.obligation_id].status}")
    return {"assessments": assessments}


def write_register(state: State) -> dict:
    """Pure assembly, no LLM. This is where traceability is attached to each finding."""
    findings = []
    for o in state["obligations"]:
        a = state["assessments"][o.obligation_id]
        chunks = state["controls"][o.obligation_id]
        findings.append(
            Finding(
                obligation_id=o.obligation_id,
                obligation_text=o.text,
                normative_force=o.normative_force,
                regulation_doc_id=state["source_name"],
                regulation_clause_path=o.clause_path,
                status=a.status,
                severity=a.severity,
                rationale=a.rationale,
                # dict.fromkeys de-duplicates while keeping rank order
                control_doc_ids=list(dict.fromkeys(c["doc_id"] for c in chunks)),
                control_chunk_ids=[c["chunk_id"] for c in chunks],
            )
        )
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.status] = counts.get(f.status, 0) + 1
    register = Register(
        source=state["source_name"],
        model=settings.gemini_model,
        top_k_controls=TOP_K_CONTROLS,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        status_counts=counts,
        findings=findings,
    )
    return {"register": register}


# --- Wiring -----------------------------------------------------------------------


def build_graph():
    g = StateGraph(State)
    g.add_node("extract_obligations", extract_obligations)
    g.add_node("retrieve_controls", retrieve_controls)
    g.add_node("assess_gaps", assess_gaps)
    g.add_node("write_register", write_register)
    g.add_edge(START, "extract_obligations")
    g.add_edge("extract_obligations", "retrieve_controls")
    g.add_edge("retrieve_controls", "assess_gaps")
    g.add_edge("assess_gaps", "write_register")
    g.add_edge("write_register", END)
    return g.compile()
