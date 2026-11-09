"""
Tests for src.database module.

Uses a temporary test database so production data is untouched.
Run: pytest tests/test_database.py -v
"""
import pytest
import tempfile
import os
from pathlib import Path

# Point DB_PATH to a temp file BEFORE importing database module
_temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
_temp_db.close()
os.environ["DB_PATH"] = _temp_db.name

# Now import — config.py will pick up the env variable
from src.database import (
    init_database,
    add_task,
    get_all_tasks,
    get_task,
    mark_complete,
    delete_task,
    get_stats,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Initialize database before each test."""
    init_database()
    yield
    # Clean up: delete all tasks
    for task in get_all_tasks(show_done=True):
        delete_task(task["id"])


class TestAddTask:
    """Tests for add_task function."""

    def test_add_task_returns_id(self):
        """Adding a task should return a valid ID."""
        task_id = add_task("Test task", "High", "Work")
        assert isinstance(task_id, int)
        assert task_id > 0

    def test_add_task_with_due_date(self):
        """Adding a task with due date should save it."""
        task_id = add_task("Test", "High", "Work", due_date="2026-12-01 10:00")
        task = get_task(task_id)
        assert task["due_date"] == "2026-12-01 10:00"

    def test_multiple_tasks(self):
        """Adding multiple tasks should create separate IDs."""
        id1 = add_task("Task 1", "High", "Work")
        id2 = add_task("Task 2", "Low", "Personal")
        assert id1 != id2


class TestGetAllTasks:
    """Tests for get_all_tasks function."""

    def test_empty_database(self):
        """Empty database should return empty list."""
        tasks = get_all_tasks()
        assert tasks == []

    def test_returns_added_tasks(self):
        """Added tasks should be returned."""
        add_task("Task A", "High", "Work")
        add_task("Task B", "Low", "Personal")

        tasks = get_all_tasks()
        assert len(tasks) == 2

    def test_filter_by_priority(self):
        """Filter by priority should work."""
        add_task("High task", "High", "Work")
        add_task("Low task", "Low", "Personal")

        high_tasks = get_all_tasks(filter_priority="High")
        assert len(high_tasks) == 1
        assert high_tasks[0]["priority"] == "High"

    def test_filter_by_category(self):
        """Filter by category should work."""
        add_task("Work task", "High", "Work")
        add_task("Health task", "Low", "Health")

        work_tasks = get_all_tasks(filter_category="Work")
        assert len(work_tasks) == 1
        assert work_tasks[0]["category"] == "Work"

    def test_completed_tasks_hidden_by_default(self):
        """Completed tasks should not show by default."""
        task_id = add_task("Test", "High", "Work")
        mark_complete(task_id)

        tasks = get_all_tasks(show_done=False)
        assert len(tasks) == 0

    def test_completed_tasks_shown_when_requested(self):
        """Completed tasks should show when show_done=True."""
        task_id = add_task("Test", "High", "Work")
        mark_complete(task_id)

        tasks = get_all_tasks(show_done=True)
        assert len(tasks) == 1

    def test_sorting_high_priority_first(self):
        """High priority tasks should come first."""
        add_task("Low task", "Low", "Personal")
        add_task("High task", "High", "Work")
        add_task("Medium task", "Medium", "Study")

        tasks = get_all_tasks()
        assert tasks[0]["priority"] == "High"
        assert tasks[1]["priority"] == "Medium"
        assert tasks[2]["priority"] == "Low"


class TestMarkComplete:
    """Tests for mark_complete function."""

    def test_mark_complete(self):
        """Marking task complete should update done flag."""
        task_id = add_task("Test", "High", "Work")
        mark_complete(task_id)

        task = get_task(task_id)
        assert task["done"] == 1
        assert task["completed_at"] is not None

    def test_mark_incomplete(self):
        """Marking task incomplete should reset done flag."""
        task_id = add_task("Test", "High", "Work")
        mark_complete(task_id, done=True)
        mark_complete(task_id, done=False)

        task = get_task(task_id)
        assert task["done"] == 0
        assert task["completed_at"] is None


class TestDeleteTask:
    """Tests for delete_task function."""

    def test_delete_task(self):
        """Deleted task should no longer exist."""
        task_id = add_task("Test", "High", "Work")
        delete_task(task_id)

        task = get_task(task_id)
        assert task is None

    def test_delete_nonexistent_task(self):
        """Deleting non-existent task should not raise."""
        delete_task(99999)  # Should not raise


class TestGetStats:
    """Tests for get_stats function."""

    def test_empty_stats(self):
        """Empty database should have zero stats."""
        stats = get_stats()
        assert stats.get("total", 0) == 0

    def test_stats_count_by_priority(self):
        """Stats should count tasks by priority."""
        add_task("Task 1", "High", "Work")
        add_task("Task 2", "High", "Personal")
        add_task("Task 3", "Low", "Study")

        stats = get_stats()
        assert stats["High"] == 2
        assert stats["Low"] == 1
        assert stats["total"] == 3

    def test_stats_excludes_completed(self):
        """Completed tasks should not be counted in priority stats."""
        id1 = add_task("Task 1", "High", "Work")
        add_task("Task 2", "Low", "Personal")
        mark_complete(id1)

        stats = get_stats()
        assert stats.get("High", 0) == 0  # Completed, excluded
        assert stats["Low"] == 1
        assert stats["total"] == 2  # Total includes completed