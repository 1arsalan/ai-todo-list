"""
Duplicate task detection using sentence embeddings.
Uses cosine similarity to find similar tasks.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer, util


# Similarity threshold (0-1). Higher = stricter.
# 0.85 means "very similar" — good for catching duplicates
SIMILARITY_THRESHOLD = 0.85

# Small, fast model (80MB). Good for semantic similarity.
MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load sentence transformer model. Cached so it loads once."""
    print(f"📥 Loading sentence embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print("✅ Model loaded.")
    return model


def find_duplicates(
    new_task: str,
    existing_tasks: list[str],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[dict]:
    """
    Find tasks in `existing_tasks` that are similar to `new_task`.

    Args:
        new_task: The task being added
        existing_tasks: List of existing task titles
        threshold: Similarity threshold (0-1). Higher = stricter.

    Returns:
        List of dicts: [{"task": str, "similarity": float}, ...]
        Sorted by similarity (highest first).
    """
    if not new_task or not existing_tasks:
        return []

    model = _load_model()

    # Encode new task + all existing tasks
    new_embedding = model.encode(new_task, convert_to_tensor=True)
    existing_embeddings = model.encode(existing_tasks, convert_to_tensor=True)

    # Compute cosine similarities
    similarities = util.cos_sim(new_embedding, existing_embeddings)[0]

    # Filter by threshold
    duplicates = []
    for idx, score in enumerate(similarities):
        score_value = float(score)
        if score_value >= threshold:
            duplicates.append({
                "task": existing_tasks[idx],
                "similarity": score_value,
            })

    # Sort by similarity (highest first)
    duplicates.sort(key=lambda x: x["similarity"], reverse=True)
    return duplicates


# ============================================================
# QUICK TEST (run: python -m src.duplicate_check)
# ============================================================
if __name__ == "__main__":
    print("🔍 Testing duplicate detection...\n")

    existing = [
        "Submit exam form",
        "Pay electricity bill",
        "Buy groceries",
        "Go to gym",
        "Watch netflix",
    ]

    test_new_tasks = [
        "Submit exam form tomorrow",   # Should match "Submit exam form"
        "Pay electricity bill today",  # Should match "Pay electricity bill"
        "Call client meeting",         # Should NOT match anything
        "Buy grocery items",           # Should match "Buy groceries"
        "Watch movie",                 # Should NOT match
    ]

    for new_task in test_new_tasks:
        dupes = find_duplicates(new_task, existing)
        print(f"New: '{new_task}'")
        if dupes:
            for d in dupes:
                print(f"  ⚠️ Similar: '{d['task']}' (score: {d['similarity']:.2f})")
        else:
            print(f"  ✅ No duplicates found")
        print()