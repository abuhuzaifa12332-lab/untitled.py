# FinSmart AI: Local Expense Analyzer

A privacy-first, locally-hosted financial analytics platform built with Python and Streamlit. It tracks expenses, visualizes financial trends via Plotly, and uses smart local heuristics to give financial advice with 100% offline security and zero premium API token costs.

---

## 🚀 Complete Local Deployment Guide

Follow these steps to deploy and run the project safely on your local machine:

### Step 1: Clone the Repository
Open your Terminal or Command Prompt (CMD) and run the following command to download the code framework:
```bash
git clone 
```

### Step 2: Install Required Dependencies
Navigate inside the project directory and install the tracking libraries from the requirements file:
```bash
pip install -r requirements-1.txt
```

### 💡 Troubleshooting (Virtual Environment setup)
If you face package permission errors or Streamlit fails to install globally, initialize a clean local python virtual wrapper:

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install streamlit plotly pandas
```

**For macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
pip install streamlit plotly pandas
```

### Step 3: Launch the App
Run this final command to make the interactive dashboard live on your local browser:
```bash
streamlit run untitled.py
```
