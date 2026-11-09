"""
One-time script to initialize the database.
Run: python scripts/setup_db.py
"""
import sys
from pathlib import Path

# Add project root to path so we can import from src
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_database, get_stats


def main():
    print("🔧 Setting up database...\n")

    # Create tables
    init_database()

    # Show current stats
    stats = get_stats()
    print(f"\n📊 Current database stats:")
    print(f"   Total tasks: {stats.get('total', 0)}")
    print(f"   High priority pending: {stats.get('High', 0)}")
    print(f"   Medium priority pending: {stats.get('Medium', 0)}")
    print(f"   Low priority pending: {stats.get('Low', 0)}")

    print("\n🎉 Setup complete! Database is ready.")
    print("Next: run the Streamlit app with:")
    print("   streamlit run app/main.py")


if __name__ == "__main__":
    main()