"""
NLP parser for extracting due dates from natural language tasks.

Examples:
    "Kal 5 baje meeting"        → task="meeting", due="<tomorrow> 17:00"
    "Submit report tomorrow"    → task="Submit report", due="<tomorrow> 00:00"
    "Buy groceries next Monday" → task="Buy groceries", due="<next Monday> 00:00"
"""
import re
from datetime import datetime
from typing import Optional

import dateparser
from dateparser.search import search_dates


# Words that indicate a date/time is present
DATE_HINT_WORDS = {
    # English
    "today", "tomorrow", "tonight", "yesterday",
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday",
    "next week", "next month",
    "am", "pm",
    # Urdu/Roman Urdu
    "aaj", "kal", "parson", "abhi", "subah", "shaam", "raat",
    "baje", "bajay",
}

# Patterns to remove from task text (case-insensitive)
DATE_PATTERNS = [
    r"\btoday\b",
    r"\btomorrow\b",
    r"\btonight\b",
    r"\byesterday\b",
    r"\baaj\b",
    r"\bkal\b",
    r"\bparson\b",
    r"\babhi\b",
    r"\bsubah\b",
    r"\bshaam\b",
    r"\braat\b",
    r"\bnext\s+week\b",
    r"\bnext\s+month\b",
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\b\d{1,2}(:\d{2})?\s*(am|pm|baje|bajay|o'?clock)\b",
    r"\bat\s+\d{1,2}(:\d{2})?\b",
    r"\bon\s+\d{1,2}(st|nd|rd|th)?\b",
    r"\b\d{1,2}(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
]

# Compile once for performance
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DATE_PATTERNS]


def _contains_date_hint(text: str) -> bool:
    """Check if text contains any date-related words."""
    text_lower = text.lower()
    return any(word in text_lower for word in DATE_HINT_WORDS)


def _clean_task_text(text: str) -> str:
    """Remove date/time words from task text."""
    cleaned = text
    for pattern in _COMPILED_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def parse_task(text: str) -> dict:
    """
    Parse a task string and extract task description + due date.

    Returns:
        {"task": str, "due_date": Optional[str]}
    """
    if not text or not text.strip():
        return {"task": "", "due_date": None}

    text = text.strip()

    # No date hint → return as-is
    if not _contains_date_hint(text):
        return {"task": text, "due_date": None}

    # Use search_dates to find date within the sentence
    try:
        matches = search_dates(
            text,
            languages=["en"],
            settings={
                "RELATIVE_BASE": datetime.now(),
                "RETURN_AS_TIMEZONE_AWARE": False,
            },
        )
    except Exception:
        matches = None

    # If no matches found, return cleaned text with no date
    if not matches:
        cleaned = _clean_task_text(text)
        return {"task": cleaned or text, "due_date": None}

    # matches is a list of (matched_text, datetime) tuples
    # Take the first match
    matched_text, parsed_date = matches[0]

    due_date = parsed_date.strftime("%Y-%m-%d %H:%M")

    # Remove the matched date text from task description
    clean_task = text.replace(matched_text, "").strip()
    clean_task = re.sub(r"\s+", " ", clean_task).strip()

    # If cleaning removed everything, fall back to original
    if not clean_task:
        clean_task = text

    return {"task": clean_task, "due_date": due_date}


# ============================================================
# QUICK TEST (run: python -m src.nlp_parser)
# ============================================================
if __name__ == "__main__":
    print("📅 Testing NLP date parser...\n")

    test_cases = [
        "Submit exam form tomorrow",
        "Kal 5 baje meeting with client",
        "Pay electricity bill today",
        "Call mom on Friday",
        "Aaj shaam 7 baje gym jana",
        "Watch netflix tonight",
        "Buy groceries next Monday",
        "Pay rent on 15th December",
        "Fix production bug",
        "Read book chapter",
    ]

    for text in test_cases:
        result = parse_task(text)
        print(f"Input:  {text}")
        print(f"  → Task: {result['task']}")
        print(f"  → Due:  {result['due_date'] or '(none)'}")
        print()