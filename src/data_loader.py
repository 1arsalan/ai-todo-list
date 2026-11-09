"""
Loads training data for models.
In professional setup, data comes from files (CSV), not hardcoded.
"""
import pandas as pd
from pathlib import Path
from src.config import RAW_DATA_DIR


def load_priority_data() -> pd.DataFrame:
    """Load priority training data from CSV."""
    file_path = RAW_DATA_DIR / "priority_training_data.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Training data not found: {file_path}")
    return pd.read_csv(file_path)


def load_category_data() -> pd.DataFrame:
    """Load category training data from CSV."""
    file_path = RAW_DATA_DIR / "category_training_data.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Training data not found: {file_path}")
    return pd.read_csv(file_path)