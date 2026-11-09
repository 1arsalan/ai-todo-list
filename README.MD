# 🤖 AI-Powered To-Do List

An intelligent to-do list application that uses machine learning 
to automatically categorize and prioritize tasks.

## Features
- AI-based priority prediction (High/Medium/Low)
- Auto category detection (Work/Personal/Health/Study)
- Natural language date parsing
- Duplicate task detection
- Clean web interface

## Tech Stack
- **Backend:** Python, scikit-learn, SQLite
- **Frontend:** Streamlit
- **ML:** TF-IDF + Logistic Regression

## Setup

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
git clone <your-repo-url>
cd ai-todo-list
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt