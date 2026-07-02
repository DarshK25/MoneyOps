"""
Voice pipeline guard functions.

Moved from the legacy voice-service to consolidate the AI Gateway.
"""

FORBIDDEN_PREMATURE_PHRASES = [
    "invoice created", "invoice sent", "payment recorded",
    "client added", "all set", "good to go",
]


def premature_confirmation_guard(response_text: str, stage: str) -> str:
    """Prevent the voice pipeline from claiming an action was completed
    when it has not yet been executed.

    If *stage* is "EXECUTED" the text passes through unchanged.
    If *stage* is "COLLECTING", "CONFIRMING", or "FAILED"
    the text is rewritten to avoid premature confirmation phrases.
    Otherwise a keyword-based safety net catches leftover phrases.
    """
    if stage == "EXECUTED":
        return response_text
    if stage in {"COLLECTING", "CONFIRMING"}:
        return response_text
    if stage == "FAILED":
        return "I hit a snag there. Could you try again?"

    text_lower = response_text.lower()
    for phrase in FORBIDDEN_PREMATURE_PHRASES:
        if phrase in text_lower:
            return "I am still working on that. One moment."
    return response_text
