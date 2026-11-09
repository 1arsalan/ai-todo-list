"""
Training script for priority and category models.
Run: python -m src.train
"""
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from src.config import PRIORITY_MODEL_PATH, CATEGORY_MODEL_PATH, MODELS_DIR
from src.data_loader import load_priority_data, load_category_data


def build_pipeline() -> Pipeline:
    """Build ML pipeline: TF-IDF + Logistic Regression."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
        ("clf", LogisticRegression(max_iter=1000))
    ])


def train_model(df, text_col, label_col, model_path, model_name):
    """Train and save a model."""
    print(f"\n{'='*50}")
    print(f"Training: {model_name}")
    print(f"{'='*50}")

    X = df[text_col]
    y = df[label_col]

    # Split: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Train
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n✅ Accuracy: {accuracy:.2%}")
    print(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")

    # Save
    MODELS_DIR.mkdir(exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)
    print(f"✅ Model saved: {model_path}")


def main():
    print("🚀 Starting training...")

    # Train priority model
    priority_df = load_priority_data()
    train_model(
        priority_df, "task", "priority",
        PRIORITY_MODEL_PATH, "Priority Model"
    )

    # Train category model
    category_df = load_category_data()
    train_model(
        category_df, "task", "category",
        CATEGORY_MODEL_PATH, "Category Model"
    )

    print(f"\n{'='*50}")
    print("🎉 All models trained successfully!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()