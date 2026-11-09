"""
Tests for src.predict module.
Run: pytest tests/test_predict.py -v
"""
import pytest

from src.predict import predict_priority, predict_category, predict_all
from src.config import PRIORITY_LEVELS, CATEGORIES


class TestPredictPriority:
    """Tests for priority prediction."""

    def test_high_priority_task(self):
        """Task with 'deadline' should be High priority."""
        result = predict_priority("Submit assignment before deadline")
        assert result == "High"

    def test_low_priority_task(self):
        """Leisure task should be Low priority."""
        result = predict_priority("Watch movie tonight")
        assert result == "Low"

    def test_returns_valid_priority(self):
        """Prediction must be one of the valid priority levels."""
        result = predict_priority("Some random task")
        assert result in PRIORITY_LEVELS

    def test_empty_text_raises_error(self):
        """Empty text should raise ValueError."""
        with pytest.raises(ValueError):
            predict_priority("")

        with pytest.raises(ValueError):
            predict_priority("   ")

    def test_none_raises_error(self):
        """None input should raise ValueError."""
        with pytest.raises(ValueError):
            predict_priority(None)


class TestPredictCategory:
    """Tests for category prediction."""

    def test_work_category(self):
        """Task with 'client meeting' should be Work."""
        result = predict_category("Client meeting at 3pm")
        assert result == "Work"

    def test_health_category(self):
        """Task with 'gym' should be Health."""
        result = predict_category("Go to gym")
        assert result == "Health"

    def test_returns_valid_category(self):
        """Prediction must be one of the valid categories."""
        result = predict_category("Some random task")
        assert result in CATEGORIES

    def test_empty_text_raises_error(self):
        """Empty text should raise ValueError."""
        with pytest.raises(ValueError):
            predict_category("")


class TestPredictAll:
    """Tests for combined prediction."""

    def test_returns_both_predictions(self):
        """predict_all should return both priority and category."""
        result = predict_all("Submit exam form tomorrow")
        assert "priority" in result
        assert "category" in result
        assert result["priority"] in PRIORITY_LEVELS
        assert result["category"] in CATEGORIES

    def test_consistency(self):
        """Two calls with same input should give same output."""
        text = "Pay electricity bill"
        result1 = predict_all(text)
        result2 = predict_all(text)
        assert result1 == result2