"""
Central configuration for the project.
All paths and constants in one place.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Models directory
MODELS_DIR = BASE_DIR / "models"

# Model file paths
PRIORITY_MODEL_PATH = MODELS_DIR / "priority_model.pkl"
CATEGORY_MODEL_PATH = MODELS_DIR / "category_model.pkl"

# Database
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "todo.db")

# App settings
APP_NAME = os.getenv("APP_NAME", "AI Todo List")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Priority levels
PRIORITY_LEVELS = ["High", "Medium", "Low"]

# Categories
CATEGORIES = ["Work", "Personal", "Health", "Study", "Entertainment"]