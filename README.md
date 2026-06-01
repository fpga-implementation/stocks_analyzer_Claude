# Stock Analyzer — Streamlit App

## Deploy to Streamlit Community Cloud (5 minutes)

### Step 1 — Push to GitHub
- github.com → New repository → name `stock-analyzer` → Private → Create
- Upload these files → Commit

### Step 2 — Deploy on Streamlit Community Cloud
- share.streamlit.io → New app
- Select your repo, branch: main, file: app.py
- Click **Advanced settings** → **Secrets** → paste:
  ```
  ANTHROPIC_API_KEY = "sk-ant-your-key-here"
  ```
- Click **Deploy**

### Step 3 — Get your API key
- platform.anthropic.com → API Keys → Create Key
- Billing → add credit card + $5 credit

### Install on Android
- Open the Streamlit URL in Chrome
- Tap ⋮ → Add to Home Screen
