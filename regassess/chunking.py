"""Structure-aware chunking: Docling items -> clause-level chunks.

Pipeline, in order:
  1. build_elements: flatten Docling items, drop noise (pictures, footnotes,
     empty watermark remnants), and strip footnote reference numbers.
  2. merge_continuations: rejoin a clause that was cut by a page break.
  3. assign paths: walk the elements keeping a stack of enclosing clause
     numbers, so "(a)" under "9.1" becomes "9.1(a)".
  4. pack: group each clause with its children into chunks of at most
     MAX_CHARS, splitting at clause boundaries, never mid-sentence.

clause_path is only ever built from numbers literally present in the source
(a Docling marker or an inline number). If a chunk's clause cannot be
identified, clause_path is None; it is never guessed.
"""

import re
import statistics
from dataclasses import dataclass, field

from docling_core.types.doc import DoclingDocument

from regassess.parsing import iter_items

MAX_CHARS = 2000  # ~450 tokens; bge-small's window is 512 tokens
MIN_CHARS = 250  # smaller fragments are merged into a neighbour when a clause is split

# Unnumbered headings that start a new part of the document, so the clause
# stack must not leak across them.
_RESETTING_HEADING = re.compile(r"^(chapter|part|annex|appendix)\b", re.IGNORECASE)

_TERMINAL = re.compile(r"""[.;:?!]["”')\]]*$""")
_ROMAN = re.compile(r"^(?=[ivxlcdm])m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$")
_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}

# Inline numbering at the start of a text.
_INLINE_DEC = re.compile(r"^(\d{1,3}(?:\.\d{1,3})+)\s+(?=\S)")  # 9.1  5.10
_INLINE_INT = re.compile(r"^(\d{1,3}[A-Z]?)\.\s+(?=\S)")  # 38.  5A.
_INLINE_PAREN = re.compile(r"^\(([a-z]{1,4}|\d{1,2})\)\s*(?=\S)")  # (a) (iv) (2)
_INLINE_BARE = re.compile(r"^([a-z]{1,4})\)\s+(?=\S)")  # a)  iv)
_INLINE_UPPER_ROMAN = re.compile(r"^([IVX]{1,4})\.\s+(?=\S)")  # I.  II.  (amendment annex headings)
_INLINE_LOWER_DOT = re.compile(r"^([a-z]{1,4})\.\s+(?=\S)")  # iia.  iii.  (headings only)
_SIGN_OFF = re.compile(
    r"^(Yours (faithfully|sincerely)\b|\([A-Z][A-Za-z.\- ]+\)\s*(Principal |Deputy |Executive )?"
    r"(Chief General Manager|General Manager|Director))"
)


# --- numbering tokens ---------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    """One level of the clause stack. kind: dec | int | letters | num."""

    kind: str
    value: str


def _roman_value(text: str) -> int:
    total = 0
    for char, nxt in zip(text, text[1:] + " "):
        value = _ROMAN_VALUES[char]
        total += -value if nxt in _ROMAN_VALUES and _ROMAN_VALUES[nxt] > value else value
    return total


def _is_successor(prev: str, new: str, as_roman: bool) -> bool:
    if as_roman:
        return _ROMAN.match(prev) and _ROMAN.match(new) and _roman_value(new) == _roman_value(prev) + 1
    return len(prev) == 1 and len(new) == 1 and ord(new) == ord(prev) + 1


def _classify_marker(marker: str) -> Entry | None:
    """Docling markers look like '5.10', '4.', 'a)', 'iv.', '1.', '·'. Bullets -> None."""
    token = marker.strip().strip("().").strip()
    if re.fullmatch(r"\d{1,3}(\.\d{1,3})+", token):
        return Entry("dec", token)
    if re.fullmatch(r"\d{1,3}", token):
        # "4." is a top-level paragraph in one place and a sub-item in another
        # (md-kyc-2016 has both); _apply decides by sequence.
        return Entry("digit", token)
    if re.fullmatch(r"[a-z]{1,4}", token):
        return Entry("letters", token)
    return None  # bullets, uppercase letters, anything we do not recognise


def _parse_numbering(label: str, marker: str, text: str, footnotes: set[int]) -> tuple[list[Entry], str]:
    """Return (numbering entries, text with a leading footnote reference removed).

    Docling fuses footnote reference numbers into the text ("5 \"Aadhaar number\"",
    "15. 54 Deleted"). A number is only removed if it matches a real footnote on
    the same page, so genuine numbers are never eaten.
    """

    def drop_ref(value: str) -> str:
        found = re.match(r"^(\d{1,3})\s+(?=\S)", value)
        if found and int(found.group(1)) in footnotes:
            return value[found.end() :]
        return value

    text = drop_ref(text)
    entries: list[Entry] = []
    from_marker = _classify_marker(marker) if marker else None
    if from_marker:
        entries.append(from_marker)

    rest, offset = text, 0
    first = True
    patterns = [(_INLINE_DEC, "dec"), (_INLINE_INT, "int"), (_INLINE_PAREN, None), (_INLINE_BARE, None)]
    if label == "section_header":
        # Only in headings: "I." in running text is far more likely a sentence fragment.
        patterns.append((_INLINE_UPPER_ROMAN, "int"))
        patterns.append((_INLINE_LOWER_DOT, None))
    for _ in range(3):
        for pattern, kind in patterns:
            found = pattern.match(rest)
            if not found:
                continue
            if kind and (from_marker or not first):
                continue  # a marker already supplied the number
            token = found.group(1)
            if kind:
                entries.append(Entry(kind, token))
            elif re.fullmatch(r"\d{1,2}", token):
                entries.append(Entry("num", token))
            else:
                entries.append(Entry("letters", token))
            offset += found.end()
            rest = text[offset:]
            # a footnote ref can follow the number: "15. 54 Deleted", "(e) 124 Due"
            dropped = drop_ref(rest)
            if dropped is not rest:
                text = text[:offset] + dropped
                rest = dropped
            first = False
            break
        else:
            break
    return entries, text


def _resolve_digit(stack: list[Entry], entry: Entry) -> Entry:
    """Decide whether a bare integer marker is a top-level paragraph or a sub-item."""
    number = int(entry.value)
    if any(held.kind == "num" and int(held.value) == number - 1 for held in stack):
        return Entry("num", entry.value)  # continues a numbered run: 1. -> 2.
    base = int(re.match(r"\d+", stack[0].value).group()) if stack else None
    if base is not None and number == base + 1:
        return Entry("int", entry.value)  # next top-level paragraph: 8 -> 9
    if number == 1 and stack:
        return Entry("num", entry.value)  # first item of a numbered sub-list
    if base is None or number > base:
        return Entry("int", entry.value)  # first paragraph after a reset, or a jump ahead
    return Entry("num", entry.value)


def _apply(stack: list[Entry], entry: Entry) -> bool:
    """Place `entry` into the clause stack. False if it has no parent to hang on."""
    if entry.kind == "digit":
        entry = _resolve_digit(stack, entry)
    if entry.kind in ("dec", "int"):
        stack[:] = [entry]
        return True
    if entry.kind == "num":
        interpretations = [("num", entry.value)]
    else:
        interpretations = []
        if len(entry.value) == 1:
            interpretations.append(("alpha", entry.value))
        if _ROMAN.match(entry.value):
            interpretations.append(("roman", entry.value))

    # 1. Successor of an enclosing entry (b after a, ii after i): its sibling.
    for depth in range(len(stack) - 1, 0 - 1, -1):
        held = stack[depth]
        for kind, value in interpretations:
            if kind == "num" and held.kind == "num" and int(value) == int(held.value) + 1:
                stack[depth:] = [Entry("num", value)]
                return True
            if held.kind == "letters" and kind != "num":
                prev_is_roman = kind == "roman"
                if _is_successor(held.value, value, prev_is_roman):
                    stack[depth:] = [Entry("letters", value)]
                    return True
    if not stack:
        return False  # sub-level number with no enclosing clause: do not guess

    # 2. First of a sequence (a, i, 1): a child of whatever is on top.
    for kind, value in interpretations:
        if (kind, value) in (("alpha", "a"), ("roman", "i"), ("num", "1")):
            stack.append(Entry("num" if kind == "num" else "letters", value))
            return True

    # 3. Neither: sibling of the deepest entry of the same kind, else a child.
    for depth in range(len(stack) - 1, 0, -1):
        if stack[depth].kind == entry.kind:
            stack[depth:] = [entry]
            return True
    stack.append(entry)
    return True


def _path_string(entries) -> str:
    head, *tail = entries
    return head.value + "".join(f"({entry.value})" for entry in tail)


# --- elements: flatten Docling items and drop noise ----------------------------

_KEPT_LABELS = {"text", "list_item", "section_header", "title", "table", "caption", "formula", "code"}
_STANDALONE_UNSPLITTABLE = re.compile(r"^(Explanation|Provided|Note|Illustration)\b")


@dataclass
class Element:
    label: str
    text: str
    marker: str
    page: int
    numbering: list[Entry]
    page_end: int = 0

    def __post_init__(self):
        self.page_end = self.page


@dataclass
class ChunkStats:
    footnote_items_dropped: int = 0
    empty_items_dropped: int = 0  # mostly watermark-only items left empty
    sign_off_dropped: int = 0
    page_break_merges: int = 0
    same_page_merges: int = 0
    unnumbered_headings: int = 0
    unplaced_numbers: int = 0  # sub-level number with no enclosing clause
    oversize_chunks: int = 0
    unterminated_chunks: int = 0
    unplaced_examples: list[str] = field(default_factory=list)  # first few, for diagnosis


def _footnote_numbers(items) -> dict[int, set[int]]:
    """Footnote numbers per page, from items Docling labelled as footnotes."""
    numbers: dict[int, set[int]] = {}
    for item, _document in items:
        if getattr(item.label, "value", item.label) != "footnote" or not item.prov:
            continue
        found = re.match(r"^(\d{1,3})\s", item.text or "")
        if found:
            numbers.setdefault(item.prov[0].page_no, set()).add(int(found.group(1)))
    return numbers


def build_elements(documents: list[DoclingDocument], doc_id: str, stats: ChunkStats) -> list[Element]:
    items = list(iter_items(documents))
    page_footnotes = _footnote_numbers(items)
    page_text: dict[int, str] = {}  # text seen so far per page, to confirm footnote refs
    footnote_page = None  # footnote lines run to the end of their page
    elements: list[Element] = []

    for item, document in items:
        label = getattr(item.label, "value", item.label)
        page = item.prov[0].page_no if item.prov else (elements[-1].page if elements else 1)
        if label == "footnote":
            stats.footnote_items_dropped += 1
            footnote_page = page
            continue
        if label not in _KEPT_LABELS:
            continue  # pictures, TOC, running headers/footers
        if label == "table":
            # Docling bakes a table's caption into its markdown. Often the caption IS a
            # clause ("17.5 A customer's liability ... limited to:"), so emit it as its
            # own text part, where it gets normal numbering, and keep the body separate.
            caption = (item.caption_text(document) or "").strip()
            markdown = item.export_to_markdown(doc=document)
            if caption:
                markdown = markdown.replace(caption, "", 1)
            # Docling pads markdown columns with runs of spaces and dashes; collapse
            # them so a table's size reflects its content, not its layout.
            body = re.sub(r"-{3,}", "---", re.sub(r"[ \t]{2,}", " ", markdown)).strip()
            parts = ([("text", caption, "")] if caption else []) + [("table", body, "")]
        else:
            parts = [(label, (item.text or "").strip(), (getattr(item, "marker", "") or "").strip())]

        for label, text, marker in parts:
            if label == "text" and not marker:
                starts_footnote = re.match(r"^(\d{1,2})\s+[A-Z]", text)
                ref_seen = starts_footnote and re.search(
                    rf"(?<=\s){starts_footnote.group(1)}(?=[\s:,.;)])", page_text.get(page, "")
                )
                if footnote_page == page or ref_seen:
                    # Footnote lines are split one per line; they run to the page end.
                    stats.footnote_items_dropped += 1
                    footnote_page = page
                    continue
            if not text:
                stats.empty_items_dropped += 1
                continue
            if label == "text" and _SIGN_OFF.match(text):
                stats.sign_off_dropped += 1  # "Yours faithfully", signatory line: not clause text
                continue

            numbering, text = _parse_numbering(label, marker, text, page_footnotes.get(page, set()))
            page_text[page] = page_text.get(page, "") + " " + text
            elements.append(Element(label, text, marker, page, numbering))
    return elements


def merge_continuations(elements: list[Element], stats: ChunkStats) -> list[Element]:
    """Rejoin text cut mid-sentence by a page break (or by Docling's line splitting).

    An unnumbered item continues the previous one only if the previous one does
    not end in terminal punctuation AND (the page changed, or it starts lowercase).
    A truncated clause carrying a clean-looking path is worse than a null one.
    """
    merged: list[Element] = []
    for element in elements:
        previous = merged[-1] if merged else None
        continues = (
            previous is not None
            and element.label in ("text", "list_item")
            and previous.label in ("text", "list_item")
            and not element.marker
            and not element.numbering
            and not _STANDALONE_UNSPLITTABLE.match(element.text)
            and not _TERMINAL.search(previous.text)
            and (element.page != previous.page_end or element.text[0].islower())
        )
        if continues:
            if element.page != previous.page_end:
                stats.page_break_merges += 1
            else:
                stats.same_page_merges += 1
            previous.text += " " + element.text
            previous.page_end = element.page
        else:
            merged.append(element)
    return merged


# --- units: one clause (with its own paragraphs) ---------------------------------


@dataclass
class Unit:
    path: tuple[Entry, ...] | None  # None = clause not identifiable
    text: str
    heading: str | None
    page_start: int
    page_end: int


def _split_table(markdown: str) -> list[str]:
    """Split a markdown table into pieces of at most MAX_CHARS, header row repeated."""
    if len(markdown) <= MAX_CHARS:
        return [markdown]
    rows = markdown.split("\n")
    header, body = rows[:2], rows[2:]
    pieces: list[list[str]] = [[]]
    size = sum(len(row) for row in header)
    for row in body:
        if pieces[-1] and size + len(row) + 1 > MAX_CHARS:
            pieces.append([])
            size = sum(len(row_) for row_ in header)
        pieces[-1].append(row)
        size += len(row) + 1
    return ["\n".join(header + piece) for piece in pieces if piece] or [markdown]


def build_units(elements: list[Element], stats: ChunkStats) -> list[Unit]:
    units: list[Unit] = []
    stack: list[Entry] = []
    heading: str | None = None
    current: Unit | None = None  # the unit an unnumbered paragraph should join

    def place(numbering: list[Entry]) -> bool:
        trial = list(stack)
        if not all(_apply(trial, entry) for entry in numbering):
            return False
        stack[:] = trial
        return True

    for element in elements:
        display = f"{element.marker} {element.text}" if element.marker else element.text

        if element.label == "section_header" and not element.numbering:
            # Unnumbered headings are context, not clauses: they set `heading`.
            stats.unnumbered_headings += 1
            heading = element.text
            if _RESETTING_HEADING.match(element.text):
                stack.clear()
                current = None
            continue

        if element.label == "table":
            # A table is its own unit under the enclosing clause, so it is retrievable
            # on its own and can never bloat the clause it sits in. Oversize tables
            # are split by rows, header repeated in each piece.
            path = tuple(stack) or None
            for piece in _split_table(display):
                units.append(Unit(path, piece, heading, element.page, element.page_end))
            continue

        if element.numbering:
            placed = place(element.numbering)
            if not placed:
                stats.unplaced_numbers += 1
                if len(stats.unplaced_examples) < 12:
                    wanted = "".join(f"[{e.kind}:{e.value}]" for e in element.numbering)
                    stats.unplaced_examples.append(
                        f"p{element.page} {wanted} stack={[e.value for e in stack]} :: {element.text[:70]}"
                    )
            if element.label == "section_header" and placed and len(stack) == 1:
                heading = element.text  # top-level headings only; sub-headings would go stale
            path = tuple(stack) if placed else None
            current = Unit(path, display, heading, element.page, element.page_end)
            units.append(current)
        elif current is not None:
            current.text += "\n" + display
            current.page_end = element.page_end
        else:
            current = Unit(tuple(stack) or None, display, heading, element.page, element.page_end)
            units.append(current)
            if not stack:
                current = None  # preamble: every paragraph stands alone
    return units


# --- packing: units -> chunks ------------------------------------------------------


def _nests(parent: tuple[Entry, ...], child: tuple[Entry, ...] | None) -> bool:
    """Is `child` a clause inside `parent`?"""
    if not child:
        return False
    if len(child) > len(parent) and child[:len(parent)] == parent:
        return True  # 38(a) inside 38; 9.1(i) inside 9.1
    # A section heading "9." contains its decimal clauses "9.1", "9.2" ...
    return (
        len(parent) == 1
        and parent[0].kind == "int"
        and child[0].kind == "dec"
        and child[0].value.split(".")[0] == parent[0].value
    )


def _subtrees(units: list[Unit]) -> list[list[Unit]]:
    """Group units into [clause + all deeper clauses nested under it]."""
    groups: list[list[Unit]] = []
    index = 0
    while index < len(units):
        head, end = units[index], index + 1
        if head.path:
            while end < len(units) and _nests(head.path, units[end].path):
                end += 1
        groups.append(units[index:end])
        index = end
    return groups


def _size(units: list[Unit]) -> int:
    return sum(len(unit.text) for unit in units) + len(units)


def _pack(units: list[Unit]) -> list[list[Unit]]:
    """Chunk groups for one clause subtree: whole if it fits, else split at child clauses."""
    if _size(units) <= MAX_CHARS or len(units) == 1:
        return [units]
    pieces = [[units[0]]] + _subtrees(units[1:])
    out: list[list[Unit]] = []
    buffer: list[Unit] = []
    for piece in pieces:
        if _size(piece) > MAX_CHARS and len(piece) > 1:
            if buffer:
                out.append(buffer)
                buffer = []
            out.extend(_pack(piece))
        elif buffer and _size(buffer) >= MIN_CHARS:
            out.append(buffer)  # the buffer is substantial on its own
            buffer = list(piece)
        elif buffer and _size(buffer) + _size(piece) > MAX_CHARS:
            out.append(buffer)
            buffer = list(piece)
        else:
            buffer.extend(piece)  # a fragment (heading line, one-line item) joins its neighbour
    if buffer:
        out.append(buffer)
    # a tiny trailing fragment rejoins the chunk before it
    if len(out) > 1 and _size(out[-1]) < MIN_CHARS and _size(out[-2]) + _size(out[-1]) <= MAX_CHARS:
        out[-2].extend(out.pop())
    return out


def pack_units(units: list[Unit]) -> list[list[Unit]]:
    groups: list[list[Unit]] = []
    unidentified: list[Unit] = []  # consecutive null-path units share chunks

    def flush():
        nonlocal unidentified
        if unidentified:
            groups.append(unidentified)
            unidentified = []

    for subtree in _subtrees(units):
        if subtree[0].path is None:
            if unidentified and _size(unidentified) + _size(subtree) > MAX_CHARS:
                flush()
            unidentified.extend(subtree)
        else:
            flush()
            groups.extend(_pack(subtree))
    flush()
    return groups


# --- public entry point ------------------------------------------------------------

_METADATA_FIELDS = ("status", "effective_from", "effective_to", "issue_date", "amended_up_to", "document_type", "amends")


@dataclass
class ChunkResult:
    chunks: list[dict] = field(default_factory=list)
    stats: ChunkStats = field(default_factory=ChunkStats)

    @property
    def null_path_count(self) -> int:
        return sum(1 for chunk in self.chunks if chunk["clause_path"] is None)

    @property
    def median_chars(self) -> float:
        return statistics.median(len(chunk["text"]) for chunk in self.chunks) if self.chunks else 0

    def depth_distribution(self) -> dict[str, int]:
        """How many chunks have a 1-, 2- or 3+-level clause_path (null excluded)."""
        counts = {"1": 0, "2": 0, "3+": 0}
        for chunk in self.chunks:
            if chunk["clause_path"] is not None:
                depth = chunk["clause_depth"]
                counts["1" if depth == 1 else "2" if depth == 2 else "3+"] += 1
        return counts

    def clause_depth_distribution(self) -> dict[str, int]:
        """Same, over every clause inside the chunks (`covers`), not just each chunk's first.

        Children are packed into their parent's chunk, so chunk-level depth alone
        hides how much of the hierarchy was actually read.
        """
        counts = {"1": 0, "2": 0, "3+": 0}
        for chunk in self.chunks:
            for path in chunk["covers"]:
                depth = 1 + path.count("(")
                counts["1" if depth == 1 else "2" if depth == 2 else "3+"] += 1
        return counts


def chunk_document(doc_id: str, documents: list[DoclingDocument], manifest_entry: dict) -> ChunkResult:
    """Chunk one parsed document. Call parsing.strip_watermark on it first."""
    result = ChunkResult()
    stats = result.stats
    elements = merge_continuations(build_elements(documents, doc_id, stats), stats)
    units = build_units(elements, stats)

    for number, group in enumerate(pack_units(units)):
        first = group[0]
        text = "\n".join(unit.text for unit in group)
        covers = [_path_string(unit.path) for unit in group if unit.path]
        if _size(group) > MAX_CHARS:
            stats.oversize_chunks += 1
        if not _TERMINAL.search(text.rstrip()):
            stats.unterminated_chunks += 1
        result.chunks.append(
            {
                "chunk_id": f"{doc_id}:{number:04d}",
                "doc_id": doc_id,
                "clause_path": _path_string(first.path) if first.path else None,
                "clause_depth": len(first.path) if first.path else 0,
                "covers": covers,
                "heading": first.heading,
                "page_start": min(unit.page_start for unit in group),
                "page_end": max(unit.page_end for unit in group),
                "text": text,
                **{key: manifest_entry.get(key) for key in _METADATA_FIELDS},
            }
        )
    return result
