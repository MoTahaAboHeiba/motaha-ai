"""
src/generation/scope_guard.py

Determines whether retrieved evidence is sufficient to warrant an LLM call.
If not, the pipeline returns a canned refusal instead of calling any LLM.

WHY top_dense_score, NOT the RRF score
---------------------------------------
RRF scores are sums of 1/(k + rank).  With k=60 and two result lists of 10
items each, the theoretical maximum is 1/61 + 1/61 ≈ 0.033.  A threshold of
0.35 on an RRF score is permanently unreachable — every query would be refused.

The dense score (cosine similarity from Qdrant) lives in [0, 1] and directly
represents semantic overlap between the query and the best-matching chunk.
0.35 cosine similarity is a defensible floor: it means the query is at least
moderately related to the retrieved content.
"""

REFUSAL = (
    "That is not something I have covered in my knowledge base yet.\n"
    "I am continuously building this out as I grow.\n\n "
    "If this is important to your evaluation, reach out to me directly "
    "and I will give you a real answer:\n"
    "Email: mohamed-aboheiba@outlook.com\n"
    "LinkedIn: linkedin.com/in/mohamed-taha-abo-heiba"
)



def is_sufficient(top_dense_score: float, threshold: float = 0.35) -> bool:
    """Return True if the top Qdrant cosine score meets the minimum threshold.

    Parameters
    ----------
    top_dense_score:
        The highest cosine similarity score returned by the dense (Qdrant)
        search before RRF fusion.  Sourced from ``retriever.retrieve()``
        under the key ``"top_dense_score"``.  Range: 0.0–1.0.
    threshold:
        Minimum cosine similarity required to proceed to LLM generation.
        Defaults to 0.35.

    Returns
    -------
    bool
        True  → semantic overlap is strong enough; proceed to LLM generation.
        False → no relevant content found; return REFUSAL to the user.
    """
    return top_dense_score >= threshold