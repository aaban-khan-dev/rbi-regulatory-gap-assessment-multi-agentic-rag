"""The NLTK English stopword list (198 words in the current release; checked equal to
`nltk.corpus.stopwords.words('english')`), embedded so no dependency or corpus
download is needed.

Chosen over scikit-learn's 318-word list because that one also removes `must`, `may`,
`should`, `not`, `no`, `within` and `per`, which carry meaning in regulation text. This
list still removes `should`, `not` and `no`, and keeps `must`, `may`, `shall`.
Contraction forms never occur as tokens (the tokenizer splits on apostrophes) but are
kept so the list is the published one. Single letters such as `a`, `i`, `s`, `t`, `d`
are in it, so clause markers like "(a)" and "(i)" are dropped too.
"""

ENGLISH_STOPWORDS = frozenset(
    """
    i me my myself we our ours ourselves you you're you've you'll you'd your yours
    yourself yourselves he him his himself she she's her hers herself it it's its itself
    they them their theirs themselves what which who whom this that that'll these those
    am is are was were be been being have has had having do does did doing a an the and
    but if or because as until while of at by for with about against between into
    through during before after above below to from up down in out on off over under
    again further then once here there when where why how all any both each few more
    most other some such no nor not only own same so than too very s t can will just
    don don't should should've now d ll m o re ve y ain aren aren't couldn couldn't
    didn didn't doesn doesn't hadn hadn't hasn hasn't haven haven't isn isn't ma mightn
    mightn't mustn mustn't needn needn't shan shan't shouldn shouldn't wasn wasn't
    weren weren't won won't wouldn wouldn't
    we'll it'd he'll he'd she'd i've it'll i'll they've we've we'd they'd she'll he's
    they'll we're i'm they're i'd
    """.split()
)
