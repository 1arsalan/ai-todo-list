"""
AI To-Do List — Streamlit Frontend (Professional Custom Auth & Multi-User)
"""
import sys
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

import streamlit as st
from datetime import datetime

# Backend imports
from src.database import (
    add_task, get_all_tasks, mark_complete, delete_task, get_stats, init_database,
    register_user, authenticate_user
)
from src.predict import predict_all
from src.nlp_parser import parse_task
from src.duplicate_check import find_duplicates
from src.config import PRIORITY_LEVELS, CATEGORIES, APP_NAME, APP_VERSION
from src.config import PRIORITY_MODEL_PATH, CATEGORY_MODEL_PATH
from src.train import main as train_main

# ==========================================
# CLOUD SETUP: Auto-train and DB init
# ==========================================
init_database()
if not PRIORITY_MODEL_PATH.exists() or not CATEGORY_MODEL_PATH.exists():
    with st.spinner("🤖 First run on cloud: Training AI models..."):
        train_main()

st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="wide")

# ==========================================
# SESSION STATE INIT (Track login)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["name"] = ""

# ==========================================
# LOGIN & SIGN UP UI
# ==========================================
if not st.session_state["logged_in"]:
    st.title("🔐 Welcome to AI To-Do List")
    st.write("Please login or create a new account to manage your tasks.")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    # --- TAB 1: LOGIN ---
    with tab1:
        with st.form("login_form"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login", use_container_width=True)
            
            if login_btn:
                user = authenticate_user(login_user, login_pass)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user["username"]
                    st.session_state["name"] = user["name"]
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. (Default: admin / admin123)")

    # --- TAB 2: SIGN UP ---
    with tab2:
        with st.form("signup_form"):
            new_name = st.text_input("Full Name")
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            new_pass_confirm = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Create Account", use_container_width=True)
            
            if signup_btn:
                if not new_name or not new_user or not new_pass:
                    st.warning("Please fill all fields.")
                elif new_pass != new_pass_confirm:
                    st.error("Passwords do not match.")
                elif len(new_pass) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    success = register_user(new_user, new_pass, new_name)
                    if success:
                        st.success("Account created successfully! Please go to the Login tab.")
                    else:
                        st.error("Username already exists. Please choose another.")

# ==========================================
# MAIN APP (Sirf Login ke baad chalega)
# ==========================================
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"🤖 {APP_NAME}")
        st.write(f"Welcome, **{st.session_state['name']}**!")
        
        if st.button("Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["name"] = ""
            st.rerun()
            
        st.markdown("---")
        st.subheader("📊 Your Stats")
        stats = get_stats(st.session_state["username"])
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("🔴 High", stats.get("High", 0))
        with col2: st.metric("🟡 Medium", stats.get("Medium", 0))
        with col3: st.metric("🟢 Low", stats.get("Low", 0))
        st.caption(f"Total tasks: **{stats.get('total', 0)}**")
        
        st.markdown("---")
        st.subheader("✨ AI Features")
        st.markdown("- 🧠 Priority prediction\n- 🏷️ Category detection\n- 📅 Date parsing\n- 🔍 Duplicate detection")

    # --- MAIN CONTENT ---
    st.title("🤖 AI-Powered To-Do List")
    st.caption("AI parses dates, predicts priority & category, and prevents duplicates.")
    st.markdown("---")

    # ADD TASK FORM
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            task_text = st.text_input("Task description", placeholder="e.g., Kal 5 baje meeting with client")
        with col2:
            override_priority = st.selectbox("Priority", ["Auto (AI)"] + PRIORITY_LEVELS)
        
        submitted = st.form_submit_button("➕ Add Task", use_container_width=True)
        
        if submitted:
            if not task_text or not task_text.strip():
                st.error("⚠️ Task text cannot be empty.")
            else:
                with st.spinner("Processing..."):
                    parsed = parse_task(task_text)
                    clean_task = parsed["task"]
                    due_date = parsed["due_date"]
                    
                    existing = get_all_tasks(st.session_state["username"], show_done=False)
                    existing_titles = [t["title"] for t in existing]
                    duplicates = find_duplicates(clean_task, existing_titles)
                    
                    if duplicates:
                        st.warning(f"⚠️ **Possible duplicate!** Similar task: **'{duplicates[0]['task']}'**")
                        st.info("If this is different, click 'Add Task' again to confirm.")
                    else:
                        predictions = predict_all(clean_task)
                        final_priority = predictions["priority"] if override_priority == "Auto (AI)" else override_priority
                        
                        add_task(st.session_state["username"], clean_task, final_priority, predictions["category"], due_date)
                        
                        msg = f"✅ Task added! Priority: {final_priority} | Category: {predictions['category']}"
                        if due_date: msg += f" | Due: {due_date}"
                        st.success(msg)
                        st.rerun()

    st.markdown("---")
    
    # TASK LIST
    st.subheader("📋 Your Tasks")
    col1, col2, col3 = st.columns(3)
    with col1: filter_priority = st.selectbox("Priority", ["All"] + PRIORITY_LEVELS, key="f_pri")
    with col2: filter_category = st.selectbox("Category", ["All"] + CATEGORIES, key="f_cat")
    with col3: show_done = st.checkbox("Show completed", key="s_done")

    tasks = get_all_tasks(
        st.session_state["username"],
        filter_priority=None if filter_priority == "All" else filter_priority,
        filter_category=None if filter_category == "All" else filter_category,
        show_done=show_done
    )

    if not tasks:
        st.info("✨ No tasks yet. Add one above to get started!")
    
    for task in tasks:
        priority = task["priority"]
        done = bool(task["done"])
        due_date = task.get("due_date")
        
        # Overdue logic
        overdue = False
        if due_date and not done:
            try:
                if datetime.fromisoformat(due_date) < datetime.now():
                    overdue = True
            except: pass
            
        pri_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")

        col1, col2, col3, col4, col5 = st.columns([0.5, 4, 1, 1.2, 1.2])
        
        with col1:
            new_done = st.checkbox("", value=done, key=f"done_{task['id']}", label_visibility="collapsed")
            if new_done != done:
                mark_complete(task["id"], new_done)
                st.rerun()

        with col2:
            title = f"~~{task['title']}~~" if done else f"**{task['title']}**"
            if overdue: title = f"🚨 {title}"
            st.markdown(title)
            if due_date:
                st.caption(f"🚨 **OVERDUE:** {due_date}" if overdue else f"📅 Due: {due_date}")
                
        with col3: st.markdown(f"{pri_emoji} {priority}")
        with col4: st.markdown(f"🏷️ {task['category']}")
        with col5:
            if st.button("🗑️", key=f"del_{task['id']}"):
                delete_task(task["id"])
                st.rerun()
        st.markdown("---")