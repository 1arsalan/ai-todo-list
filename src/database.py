"""
Database operations for AI To-Do List.
All SQLite interactions go through this module. (Professional Multi-User Supported)
"""
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Rows as dict-like objects
    return conn


def hash_password(password: str) -> str:
    """Hash password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_database() -> None:
    """Create tables for Users and Tasks if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. USERS TABLE (Login/Signup ke liye)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 2. TASKS TABLE (Multi-user tasks)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            category TEXT NOT NULL,
            due_date TEXT,
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    # Default Admin User create karein (Agar pehle se nahi hai)
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, name, created_at) VALUES (?, ?, ?, ?)",
                       ("admin", hash_password("admin123"), "Admin Arsalan", datetime.now().isoformat()))

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")


# ==========================================
# USER AUTHENTICATION FUNCTIONS
# ==========================================
def register_user(username: str, password: str, name: str) -> bool:
    """New user register karein."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, name, created_at) VALUES (?, ?, ?, ?)",
                       (username, hash_password(password), name, datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Login check karein."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                   (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


# ==========================================
# TASK FUNCTIONS
# ==========================================
def add_task(username: str, title: str, priority: str, category: str, due_date: Optional[str] = None) -> int:
    """Insert a new task for a specific user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (user_id, title, priority, category, due_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, title, priority, category, due_date, datetime.now().isoformat()))

    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_all_tasks(username: str, filter_priority: Optional[str] = None, filter_category: Optional[str] = None, show_done: bool = False) -> list[dict]:
    """Fetch tasks for a specific user with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [username]

    if filter_priority:
        query += " AND priority = ?"
        params.append(filter_priority)

    if filter_category:
        query += " AND category = ?"
        params.append(filter_category)

    if not show_done:
        query += " AND done = 0"

    query += """
        ORDER BY
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END,
            due_date ASC,
            created_at DESC
    """

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_task(task_id: int) -> Optional[dict]:
    """Fetch a single task by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_complete(task_id: int, done: bool = True) -> None:
    """Mark a task as complete or incomplete."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET done = ?, completed_at = ? WHERE id = ?",
        (1 if done else 0, datetime.now().isoformat() if done else None, task_id)
    )
    conn.commit()
    conn.close()


def delete_task(task_id: int) -> None:
    """Delete a task by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_stats(username: str) -> dict:
    """Return statistics: pending tasks by priority for a specific user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT priority, COUNT(*) as count
        FROM tasks
        WHERE done = 0 AND user_id = ?
        GROUP BY priority
    """, (username,))
    stats = {row["priority"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = ?", (username,))
    stats["total"] = cursor.fetchone()["total"]

    conn.close()
    return stats