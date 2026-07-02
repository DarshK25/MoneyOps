FORBIDDEN_PREMATURE_PHRASES = [
    "invoice created", "invoice sent", "payment recorded",
    "client added", "all set", "good to go",
]

def premature_confirmation_guard(response_text: str, stage: str) -> str:
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
