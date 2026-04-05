# Language Detection
# Detects English vs Swahili for bilingual responses

SWAHILI_MARKERS = [
    "habari", "karibu", "asante", "tafadhali", "dawa", "hospitali",
    "mgonjwa", "daktari", "msaada", "afya",
]

def detect_language(text: str) -> str:
    text_lower = text.lower()
    swahili_count = sum(1 for word in SWAHILI_MARKERS if word in text_lower)
    return "sw" if swahili_count >= 2 else "en"

def get_response_language_hint(text: str) -> str:
    lang = detect_language(text)
    if lang == "sw":
        return "Respond in Swahili. Keep medical terms accurate."
    return "Respond in English."
