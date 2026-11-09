"""
NLP parser for extracting due dates from natural language tasks.

Examples:
    "Kal 5 baje meeting"        → task="meeting", due="<tomorrow> 17:00"
    "Submit report tomorrow"    → task="Submit report", due="<tomorrow> 00:00"
    "Buy groceries next Monday" → task="Buy groceries", due="<next Monday> 00:00"
    "Pay bill on 15th December" → task="Pay bill", due="<15 Dec> 00:00"
"""
import re
from datetime import datetime
from typing import Optional

import dateparser


# Words that indicate a date/time is present
DATE_HINT_WORDS = {
    # English
    "today", "tomorrow", "tonight", "yesterday",
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday",
    "next week", "next month", "next monday",
    "am", "pm",
    # Urdu/Roman Urdu
    "aaj", "kal", "parson", "abhi", "subah", "shaam", "raat",
    "baje", "bajay",
}

# Regex to detect time patterns like "5 baje", "5:30", "17:00", "5pm"
TIME_PATTERN = re.compile(
    r"\b\d{1,2}(:\d{2})?\s*(am|pm|baje|bajay|o'?clock)?\b",
    re.IGNORECASE,
)


def _contains_date_hint(text: str) -> bool:
    """Check if text contains any date-related words."""
    text_lower = text.lower()
    return any(word in text_lower for word in DATE_HINT_WORDS)


def _clean_task_text(text: str) -> str:
    """Remove date/time words from task text."""
    cleaned = text

    # Remove common date/time words
    date_words = [
        r"\btoday\b", r"\btomorrow\b", r"\btonight\b", r"\byesterday\b",
        r"\baaj\b", r"\bkal\b", r"\bparson\b", r"\babhi\b",
        r"\bsubah\b", r"\bshaam\b", r"\braat\b",
        r"\bnext\s+week\b", r"\bnext\s+month\b",
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b\d{1,2}(:\d{2})?\s*(am|pm|baje|bajay|o'?clock)\b",
        r"\bat\s+\d{1,2}(:\d{2})?\b",
        r"\bon\s+\d{1,2}(st|nd|rd|th)?\b",
    ]
    for pattern in date_words:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Collapse multiple spaces and strip
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def parse_task(text: str) -> dict:
    """
    Parse a task string and extract:
        - task: the clean task description
        - due_date: ISO datetime string or None

    Returns:
        {"task": str, "due_date": Optional[str]}
    """
    if not text or not text.strip():
        return {"task": "", "due_date": None}

    text = text.strip()

    # Check if any date hint exists
    if not _contains_date_hint(text):
        return {"task": text, "due_date": None}

    # Try to parse date using dateparser
    parsed = dateparser.parse(
        text,
        languages=["en", "ur"],
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now(),
            "RETURN_AS_TIMEZONE_AWARE": False,
        },
    )

    if not parsed:
        return {"task": text, "due_date": None}

    # Format as ISO string
    due_date = parsed.strftime("%Y-%m-%d %H:%M")

    # Clean task text (remove date words)
    clean_task = _clean_task_text(text)

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
        "Fix production bug",  # no date
        "Read book chapter",
    ]

    for text in test_cases:
        result = parse_task(text)
        print(f"Input:  {text}")
        print(f"  → Task: {result['task']}")
        print(f"  → Due:  {result['due_date'] or '(none)'}")
        print()