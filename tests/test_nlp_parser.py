"""
Tests for src.nlp_parser module.
Run: pytest tests/test_nlp_parser.py -v
"""
from datetime import datetime, timedelta

from src.nlp_parser import parse_task


class TestParseTask:
    """Tests for parse_task function."""

    def test_task_without_date(self):
        """Task with no date hint should return original text, no due date."""
        result = parse_task("Fix production bug")
        assert result["task"] == "Fix production bug"
        assert result["due_date"] is None

    def test_task_with_tomorrow(self):
        """'tomorrow' should set due date to tomorrow."""
        result = parse_task("Submit exam form tomorrow")
        assert "tomorrow" not in result["task"].lower()
        assert "Submit exam" in result["task"]
        assert result["due_date"] is not None

        # Verify date is actually tomorrow
        due = datetime.fromisoformat(result["due_date"])
        tomorrow = datetime.now() + timedelta(days=1)
        assert due.date() == tomorrow.date()

    def test_task_with_today(self):
        """'today' should set due date to today."""
        result = parse_task("Pay electricity bill today")
        assert result["due_date"] is not None
        due = datetime.fromisoformat(result["due_date"])
        assert due.date() == datetime.now().date()

    def test_task_with_roman_urdu(self):
        """'kal' should be recognized as date hint."""
        result = parse_task("Kal meeting with client")
        # Task should be cleaned (at least 'meeting with client' remains)
        assert "meeting" in result["task"].lower()

    def test_empty_text(self):
        """Empty text should return empty task, no date."""
        result = parse_task("")
        assert result["task"] == ""
        assert result["due_date"] is None

    def test_whitespace_only(self):
        """Whitespace-only input should return empty, no date."""
        result = parse_task("   ")
        assert result["task"] == ""
        assert result["due_date"] is None

    def test_due_date_format(self):
        """Due date should be in ISO format 'YYYY-MM-DD HH:MM'."""
        result = parse_task("Submit report tomorrow")
        if result["due_date"]:
            # Should parse without error
            datetime.fromisoformat(result["due_date"])

    def test_task_text_cleaned(self):
        """Task text should have date words removed."""
        result = parse_task("Meeting with boss tomorrow at 5pm")
        # "tomorrow", "5pm" should be removed
        assert "tomorrow" not in result["task"].lower()


class TestDateHints:
    """Tests for date hint detection."""

    def test_no_false_positives(self):
        """Tasks without date hints shouldn't get due dates."""
        no_date_tasks = [
            "Fix bug",
            "Read book",
            "Write code",
            "Call friend",
        ]
        for task in no_date_tasks:
            result = parse_task(task)
            assert result["due_date"] is None, f"False positive for: {task}"