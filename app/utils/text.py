import re
from collections import Counter


WHITESPACE_RE = re.compile(r"\s+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
MONEY_RE = re.compile(r"(?:USD|EUR|GBP|INR|\$|€|£|₹)\s?\d[\d,]*(?:\.\d{1,2})?")
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b")
NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")
ORG_RE = re.compile(
    r"\b[A-Z][A-Za-z&.,-]+(?:\s+[A-Z][A-Za-z&.,-]+)*\s+"
    r"(?:Inc|LLC|Ltd|Limited|Corporation|Corp|Company|University|Bank|Agency|Committee|Ministry)\b"
)
LOCATION_RE = re.compile(
    r"\b(?:New York|London|Paris|Delhi|Mumbai|Bangalore|San Francisco|California|Texas|Berlin|Tokyo)\b",
    re.IGNORECASE,
)
STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "have", "were", "will", "your", "into",
    "their", "about", "which", "would", "there", "been", "document", "page", "pages", "after",
    "shall", "could", "should", "than", "when", "where", "what", "while", "because", "such",
}
POSITIVE_WORDS = {
    "good", "great", "excellent", "positive", "growth", "success", "improved", "benefit", "strong",
    "efficient", "progress", "gain", "satisfied", "approved", "award", "happy",
}
NEGATIVE_WORDS = {
    "bad", "poor", "negative", "loss", "delay", "risk", "issue", "decline", "failed", "failure",
    "complaint", "critical", "concern", "problem", "penalty", "sad",
}


def clean_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def split_sentences(text: str) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    return [sentence.strip() for sentence in SENTENCE_RE.split(cleaned) if sentence.strip()]


def summarize_text(text: str, max_sentences: int = 3) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
    return " ".join(sentences[:max_sentences])


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    counts = Counter(word for word in words if word not in STOPWORDS)
    return [word for word, _ in counts.most_common(limit)]


def classify_sentiment(text: str) -> str:
    lowered = text.lower()
    positive_hits = sum(word in lowered for word in POSITIVE_WORDS)
    negative_hits = sum(word in lowered for word in NEGATIVE_WORDS)
    if positive_hits > negative_hits:
        return "positive"
    if negative_hits > positive_hits:
        return "negative"
    return "neutral"


def unique_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for match in pattern.findall(text):
        value = match if isinstance(match, str) else match[0]
        normalized = clean_text(value)
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            items.append(normalized)
    return items
