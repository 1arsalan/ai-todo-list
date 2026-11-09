"""
AI To-Do List — Streamlit Frontend

This is the UI layer. It calls backend functions from:
- src.database  (add/get/update/delete tasks)
- src.predict   (AI priority + category predictions)
"""
import streamlit as st
from datetime import datetime

# Import backend functions
from src.database import (
    add_task,
    get_all_tasks,
    mark_complete,
    delete_task,
    get_stats,
    get_task,
)
from src.predict import predict_all
from src.config import PRIORITY_LEVELS, CATEGORIES, APP_NAME, APP_VERSION


# ============================================================
# PAGE CONFIG (must be first Streamlit call)
# ============================================================
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SIDEBAR — Stats & Info
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.title(f"🤖 {APP_NAME}")
        st.caption(f"Version {APP_VERSION}")
        st.markdown("---")

        st.subheader("📊 Stats")
        stats = get_stats()
        total = stats.get("total", 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔴 High", stats.get("High", 0))
        with col2:
            st.metric("🟡 Medium", stats.get("Medium", 0))
        with col3:
            st.metric("🟢 Low", stats.get("Low", 0))

        st.caption(f"Total tasks: **{total}**")

        st.markdown("---")
        st.subheader("ℹ️ How it works")
        st.markdown(
            """
            **AI models trained on your tasks:**
            - Priority prediction (High/Medium/Low)
            - Category detection (Work/Personal/Health/Study/Entertainment)

            Just type a task — AI does the rest!
            """
        )


# ============================================================
# ADD TASK SECTION
# ============================================================
def render_add_task():
    st.subheader("➕ Add New Task")

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            task_text = st.text_input(
                "Task description",
                placeholder="e.g., Submit exam form tomorrow",
                help="Type naturally — AI will predict priority and category",
            )

        with col2:
            override_priority = st.selectbox(
                "Priority",
                ["Auto (AI)"] + PRIORITY_LEVELS,
                help="Leave as 'Auto' to let AI decide",
            )

        submitted = st.form_submit_button("➕ Add Task", use_container_width=True)

        if submitted:
            if not task_text or not task_text.strip():
                st.error("⚠️ Task text cannot be empty.")
                return

            # AI prediction
            try:
                with st.spinner("🧠 AI is analyzing..."):
                    predictions = predict_all(task_text)
            except Exception as e:
                st.error(f"Prediction failed: {e}")
                return

            ai_priority = predictions["priority"]
            ai_category = predictions["category"]

            # Override if user chose manual priority
            final_priority = (
                ai_priority if override_priority == "Auto (AI)" else override_priority
            )

            # Save to database
            task_id = add_task(
                title=task_text.strip(),
                priority=final_priority,
                category=ai_category,
                due_date=None,  # NLP parser will add this in Phase 4
            )

            st.success(
                f"✅ Task added! (ID: {task_id})  \n"
                f"**Priority:** {final_priority}  |  **Category:** {ai_category}"
            )

            # Show if manual override was used
            if override_priority != "Auto (AI)" and override_priority != ai_priority:
                st.info(f"ℹ️ AI suggested '{ai_priority}', you chose '{override_priority}'")

            st.rerun()


# ============================================================
# TASK LIST SECTION
# ============================================================
def render_task_list():
    st.subheader("📋 Your Tasks")

    # ---- Filters ----
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_priority = st.selectbox(
            "Filter by Priority",
            ["All"] + PRIORITY_LEVELS,
            key="filter_priority",
        )
    with col2:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"] + CATEGORIES,
            key="filter_category",
        )
    with col3:
        show_done = st.checkbox("Show completed", value=False, key="show_done")

    # ---- Fetch tasks ----
    tasks = get_all_tasks(
        filter_priority=None if filter_priority == "All" else filter_priority,
        filter_category=None if filter_category == "All" else filter_category,
        show_done=show_done,
    )

    if not tasks:
        st.info("✨ No tasks yet. Add one above to get started!")
        return

    st.caption(f"Showing **{len(tasks)}** task(s)")

    # ---- Render each task ----
    for task in tasks:
        render_task_card(task)


def render_task_card(task: dict):
    """Render a single task as a card."""
    priority = task["priority"]
    category = task["category"]
    done = task["done"]

    # Priority color emoji
    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")

    # Layout: [checkbox | task text | priority | category | buttons]
    col1, col2, col3, col4, col5 = st.columns([0.5, 4, 1, 1.2, 1.2])

    with col1:
        # Checkbox to toggle completion
        new_done = st.checkbox(
            "",
            value=bool(done),
            key=f"done_{task['id']}",
            label_visibility="collapsed",
        )
        if new_done != bool(done):
            mark_complete(task["id"], new_done)
            st.rerun()

    with col2:
        if done:
            st.markdown(f"~~{task['title']}~~")
        else:
            st.markdown(f"**{task['title']}**")

        # Show created time as caption
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
# MAIN APP
# ============================================================
def main():
    render_sidebar()

    st.title("🤖 AI-Powered To-Do List")
    st.caption("Type any task — AI predicts priority and category automatically.")

    st.markdown("---")

    render_add_task()

    st.markdown("---")

    render_task_list()

    # Footer
    st.markdown("---")
    st.caption(
        "Built with Streamlit + scikit-learn | Phase 3 of 6 complete | "
        "Next: NLP date parsing & duplicate detection"
    )


if __name__ == "__main__":
    main()