"""
AI To-Do List — Streamlit Frontend (Phase 4)

Now includes:
- NLP date parsing
- Duplicate detection
- Due date display + overdue highlighting
"""
import sys
from pathlib import Path

# Project root ko sys.path mein add karein
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

# Ab baaki imports
import streamlit as st
from datetime import datetime

# Backend imports
from src.database import (
    add_task,
    get_all_tasks,
    mark_complete,
    delete_task,
    get_stats,
)
from src.predict import predict_all
from src.nlp_parser import parse_task
from src.duplicate_check import find_duplicates
from src.config import PRIORITY_LEVELS, CATEGORIES, APP_NAME, APP_VERSION


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HELPERS
# ============================================================
def is_overdue(due_date_str: str | None, done: bool) -> bool:
    """Check if a task is overdue (due date in the past and not done)."""
    if not due_date_str or done:
        return False
    try:
        due = datetime.fromisoformat(due_date_str)
        return due < datetime.now()
    except Exception:
        return False


def format_due_date(due_date_str: str | None) -> str:
    """Format due date nicely."""
    if not due_date_str:
        return ""
    try:
        due = datetime.fromisoformat(due_date_str)
        return due.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return due_date_str


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.title(f"🤖 {APP_NAME}")
        st.caption(f"Version {APP_VERSION}")
        st.markdown("---")

        st.subheader("📊 Stats")
        stats = get_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔴 High", stats.get("High", 0))
        with col2:
            st.metric("🟡 Medium", stats.get("Medium", 0))
        with col3:
            st.metric("🟢 Low", stats.get("Low", 0))

        st.caption(f"Total tasks: **{stats.get('total', 0)}**")

        st.markdown("---")
        st.subheader("✨ AI Features")
        st.markdown(
            """
            - 🧠 **Priority prediction**
            - 🏷️ **Category detection**
            - 📅 **Date parsing** ("kal 5 baje")
            - 🔍 **Duplicate detection**
            """
        )


# ============================================================
# ADD TASK
# ============================================================
def render_add_task():
    st.subheader("➕ Add New Task")

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            task_text = st.text_input(
                "Task description",
                placeholder="e.g., Kal 5 baje meeting with client",
                help="Type naturally — AI will parse date, predict priority & category",
            )

        with col2:
            override_priority = st.selectbox(
                "Priority",
                ["Auto (AI)"] + PRIORITY_LEVELS,
            )

        submitted = st.form_submit_button("➕ Add Task", use_container_width=True)

        if submitted:
            if not task_text or not task_text.strip():
                st.error("⚠️ Task text cannot be empty.")
                return

            # ---- 1. Parse date & clean task ----
            with st.spinner("📅 Parsing date..."):
                parsed = parse_task(task_text)

            clean_task = parsed["task"]
            due_date = parsed["due_date"]

            # ---- 2. Duplicate check ----
            existing = get_all_tasks(show_done=False)
            existing_titles = [t["title"] for t in existing]

            with st.spinner("🔍 Checking for duplicates..."):
                duplicates = find_duplicates(clean_task, existing_titles)

            if duplicates:
                st.warning(
                    f"⚠️ **Possible duplicate detected!**  \n"
                    f"Similar task: **'{duplicates[0]['task']}'** "
                    f"(similarity: {duplicates[0]['similarity']:.0%})"
                )
                st.info("If this is different, click 'Add Task' again to confirm.")
                return

            # ---- 3. AI predictions ----
            with st.spinner("🧠 AI is analyzing..."):
                predictions = predict_all(clean_task)

            ai_priority = predictions["priority"]
            ai_category = predictions["category"]

            final_priority = (
                ai_priority
                if override_priority == "Auto (AI)"
                else override_priority
            )

            # ---- 4. Save ----
            task_id = add_task(
                title=clean_task,
                priority=final_priority,
                category=ai_category,
                due_date=due_date,
            )

            # ---- 5. Success message ----
            msg = (
                f"✅ Task added! (ID: {task_id})  \n"
                f"**Priority:** {final_priority} | **Category:** {ai_category}"
            )
            if due_date:
                msg += f"  \n📅 **Due:** {format_due_date(due_date)}"
            if clean_task != task_text.strip():
                msg += f"  \n✂️ Original: _{task_text.strip()}_"
            st.success(msg)

            if override_priority != "Auto (AI)" and override_priority != ai_priority:
                st.info(
                    f"ℹ️ AI suggested '{ai_priority}', you chose '{override_priority}'"
                )

            st.rerun()


# ============================================================
# TASK LIST
# ============================================================
def render_task_list():
    st.subheader("📋 Your Tasks")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_priority = st.selectbox(
            "Priority", ["All"] + PRIORITY_LEVELS, key="filter_priority"
        )
    with col2:
        filter_category = st.selectbox(
            "Category", ["All"] + CATEGORIES, key="filter_category"
        )
    with col3:
        show_done = st.checkbox("Show completed", value=False, key="show_done")

    tasks = get_all_tasks(
        filter_priority=None if filter_priority == "All" else filter_priority,
        filter_category=None if filter_category == "All" else filter_category,
        show_done=show_done,
    )

    if not tasks:
        st.info("✨ No tasks yet. Add one above to get started!")
        return

    st.caption(f"Showing **{len(tasks)}** task(s)")

    for task in tasks:
        render_task_card(task)


def render_task_card(task: dict):
    priority = task["priority"]
    category = task["category"]
    done = bool(task["done"])
    due_date = task.get("due_date")
    overdue = is_overdue(due_date, done)

    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")

    col1, col2, col3, col4, col5 = st.columns([0.5, 4, 1, 1.2, 1.2])

    with col1:
        new_done = st.checkbox(
            "", value=done, key=f"done_{task['id']}", label_visibility="collapsed"
        )
        if new_done != done:
            mark_complete(task["id"], new_done)
            st.rerun()

    with col2:
        title = f"~~{task['title']}~~" if done else f"**{task['title']}**"
        if overdue:
            title = f"🚨 {title}"
        st.markdown(title)

        if due_date:
            due_display = format_due_date(due_date)
            if overdue:
                st.caption(f"🚨 **OVERDUE:** {due_display}")
            else:
                st.caption(f"📅 Due: {due_display}")

        created = task.get("created_at", "")
        if created:
            try:
                created_dt = datetime.fromisoformat(created)
                st.caption(f"Created: {created_dt.strftime('%Y-%m-%d %H:%M')}")
            except Exception:
                pass

    with col3:
        st.markdown(f"{priority_emoji} {priority}")

    with col4:
        st.markdown(f"🏷️ {category}")

    with col5:
        if st.button("🗑️", key=f"del_{task['id']}", help="Delete task"):
            delete_task(task["id"])
            st.rerun()

    st.markdown("---")


# ============================================================
# MAIN
# ============================================================
def main():
    render_sidebar()

    st.title("🤖 AI-Powered To-Do List")
    st.caption(
        "AI parses dates, predicts priority & category, and prevents duplicates."
    )

    st.markdown("---")

    render_add_task()

    st.markdown("---")

    render_task_list()

    st.markdown("---")
    st.caption(
        "Built with Streamlit + scikit-learn + sentence-transformers | "
        "Phase 4 of 6 complete"
    )


if __name__ == "__main__":
    main()