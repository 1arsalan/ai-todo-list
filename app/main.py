"""
AI To-Do List — Streamlit Frontend (Professional Auth with Sign Up & Forgot Password)
"""
import sys
from pathlib import Path

# Project root ko sys.path mein add karein
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

import streamlit as st
from datetime import datetime
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# Backend imports
from src.database import (
    add_task, get_all_tasks, mark_complete, delete_task, get_stats, init_database
)
from src.predict import predict_all
from src.nlp_parser import parse_task
from src.duplicate_check import find_duplicates
from src.config import PRIORITY_LEVELS, CATEGORIES, APP_NAME, APP_VERSION
from src.config import MODELS_DIR, PRIORITY_MODEL_PATH, CATEGORY_MODEL_PATH
from src.train import main as train_main

# ==========================================
# CLOUD SETUP: Auto-train and DB init
# ==========================================
init_database()
if not PRIORITY_MODEL_PATH.exists() or not CATEGORY_MODEL_PATH.exists():
    with st.spinner("🤖 First run on cloud: Training AI models... This takes ~30 seconds."):
        train_main()

st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="wide")

# ==========================================
# AUTHENTICATION SETUP (Config File Load)
# ==========================================
config_path = root_path / "config.yaml"
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# FIX: pre_authorized ko Authenticate class se hata diya gaya hai
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def is_overdue(due_date_str: str | None, done: bool) -> bool:
    if not due_date_str or done: return False
    try:
        due = datetime.fromisoformat(due_date_str)
        return due < datetime.now()
    except Exception:
        return False

def format_due_date(due_date_str: str | None) -> str:
    if not due_date_str: return ""
    try:
        due = datetime.fromisoformat(due_date_str)
        return due.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return due_date_str

def save_config():
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

# ==========================================
# SIDEBAR (Sirf Login ke baad dikhega)
# ==========================================
if st.session_state.get("authentication_status"):
    with st.sidebar:
        st.title(f"🤖 {APP_NAME}")
        st.write(f"Welcome, **{st.session_state['name']}**!")
        authenticator.logout("Logout", "sidebar")
        st.markdown("---")
        
        st.subheader("📊 Stats")
        stats = get_stats(st.session_state['username'])
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("🔴 High", stats.get("High", 0))
        with col2: st.metric("🟡 Medium", stats.get("Medium", 0))
        with col3: st.metric("🟢 Low", stats.get("Low", 0))
        st.caption(f"Total tasks: **{stats.get('total', 0)}**")
        
        st.markdown("---")
        st.subheader("✨ AI Features")
        st.markdown("- 🧠 Priority prediction\n- 🏷️ Category detection\n- 📅 Date parsing\n- 🔍 Duplicate detection")

# ==========================================
# LOGIN / SIGN UP / FORGOT PASSWORD
# ==========================================
# FIX: Naye version ke liye sahi syntax
name, authentication_status, username = authenticator.login(
    location='main',
    fields={'Form name': 'Login', 'Username': 'Username', 'Password': 'Password', 'Login': 'Login'}
)

if authentication_status == False:
    st.error("Username/password is incorrect")
    
elif authentication_status == None:
    st.warning("Please enter your username and password")
    
    # SIGN UP SECTION
    with st.expander("Don't have an account? Sign Up"):
        try:
            # FIX: pre_authorized ab register_user mein pass hota hai
            email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(
                location='main', 
                pre_authorized=config['pre-authorized']['emails'],
                captcha=False
            )
            if email_of_registered_user:
                st.success('User registered successfully! Please proceed to login.')
                save_config()
        except Exception as e:
            st.error(e)

    # FORGOT PASSWORD SECTION
    with st.expander("Forgot Password?"):
        try:
            username_of_forgotten_password, email_of_forgotten_password, new_random_password = authenticator.forgot_password(location='main')
            if username_of_forgotten_password:
                st.success('New password generated. Please check the logs or contact support.')
                st.info(f"New Password: **{new_random_password}**") 
                save_config()
            elif username_of_forgotten_password == False:
                st.error('Username not found')
        except Exception as e:
            st.error(e)

elif authentication_status == True:
    # ==========================================
    # MAIN APP (Sirf Login ke baad chalega)
    # ==========================================
    
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
                    
                    existing = get_all_tasks(username, show_done=False)
                    existing_titles = [t["title"] for t in existing]
                    duplicates = find_duplicates(clean_task, existing_titles)
                    
                    if duplicates:
                        st.warning(f"⚠️ **Possible duplicate!** Similar task: **'{duplicates[0]['task']}'**")
                        st.info("If this is different, click 'Add Task' again to confirm.")
                    else:
                        predictions = predict_all(clean_task)
                        final_priority = predictions["priority"] if override_priority == "Auto (AI)" else override_priority
                        
                        add_task(username, clean_task, final_priority, predictions["category"], due_date)
                        
                        msg = f"✅ Task added! Priority: {final_priority} | Category: {predictions['category']}"
                        if due_date: msg += f" | Due: {format_due_date(due_date)}"
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
        username,
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
        overdue = is_overdue(due_date, done)
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
                st.caption(f"🚨 **OVERDUE:** {format_due_date(due_date)}" if overdue else f"📅 Due: {format_due_date(due_date)}")
                
        with col3: st.markdown(f"{pri_emoji} {priority}")
        with col4: st.markdown(f"🏷️ {task['category']}")
        with col5:
            if st.button("🗑️", key=f"del_{task['id']}"):
                delete_task(task["id"])
                st.rerun()
        st.markdown("---")