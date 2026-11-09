"""
Prediction wrapper for trained ML models.
Loads models once and provides simple prediction functions.
"""
import pickle
from functools import lru_cache
from pathlib import Path

from src.config import PRIORITY_MODEL_PATH, CATEGORY_MODEL_PATH


@lru_cache(maxsize=1)
def _load_model(model_path: Path):
    """Load a model from disk. Cached so it loads only once."""
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}\n"
            f"Please run: python -m src.train"
        )
    with open(model_path, "rb") as f:
        return pickle.load(f)


def predict_priority(task_text: str) -> str:
    """
    Predict priority for a task text.
    Returns: 'High', 'Medium', or 'Low'
    """
    if not task_text or not task_text.strip():
        raise ValueError("Task text cannot be empty")

    model = _load_model(PRIORITY_MODEL_PATH)
    return model.predict([task_text])[0]


def predict_category(task_text: str) -> str:
    """
    Predict category for a task text.
    Returns: 'Work', 'Personal', 'Health', 'Study', or 'Entertainment'
    """
    if not task_text or not task_text.strip():
        raise ValueError("Task text cannot be empty")

    model = _load_model(CATEGORY_MODEL_PATH)
    return model.predict([task_text])[0]


def predict_all(task_text: str) -> dict:
    """
    Predict both priority and category.
    Returns dict: {'priority': ..., 'category': ...}
    """
    return {
        "priority": predict_priority(task_text),
        "category": predict_category(task_text),
    }


# Quick test
if __name__ == "__main__":
    print("🧠 Testing prediction functions...\n")

    test_tasks = [
        "Submit exam form tomorrow",
        "Watch netflix tonight",
        "Pay electricity bill",
        "Buy groceries",
        "Go to gym",
    ]

    for task in test_tasks:
        result = predict_all(task)
        print(f"'{task}'")
        print(f"  → Priority: {result['priority']}")
        print(f"  → Category: {result['category']}\n")

    print("🎉 Prediction working!")