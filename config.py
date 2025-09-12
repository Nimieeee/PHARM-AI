"""
Configuration settings for PharmGPT
"""

import streamlit as st

# API Configuration - Only use Streamlit secrets (secure for both local and cloud)
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError as e:
    st.error(f"Missing API key in Streamlit secrets: {e}")
    st.info("Please add your API keys to Streamlit secrets or .streamlit/secrets.toml file")
    GROQ_API_KEY = None
    OPENROUTER_API_KEY = None

# Model configurations
MODEL_CONFIGS = {
    "normal": {
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "api_key": GROQ_API_KEY,
        "base_url": "https://api.groq.com/openai/v1",
        "description": "Llama 4 Maverick (Balanced)"
    },
    "turbo": {
        "model": "openrouter/sonoma-sky-alpha",
        "api_key": OPENROUTER_API_KEY,
        "base_url": "https://openrouter.ai/api/v1",
        "description": "Sonoma Sky Alpha (Fast)"
    }
}

# Application settings
APP_TITLE = "PharmGPT - AI Pharmacology Assistant"
APP_ICON = "💊"

# File upload settings
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ['pdf', 'txt', 'csv', 'docx', 'doc', 'png', 'jpg', 'jpeg']

# Database settings - Supabase only
USE_SUPABASE = True  # Always use Supabase (file-based storage removed)

# Supabase configuration (loaded from secrets)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
except KeyError as e:
    st.error(f"Missing Supabase configuration in Streamlit secrets: {e}")
    st.info("Please add SUPABASE_URL and SUPABASE_ANON_KEY to your Streamlit secrets")
    SUPABASE_URL = None
    SUPABASE_ANON_KEY = None

# Upload settings
UPLOAD_LIMIT_PER_DAY = -1  # -1 means unlimited uploads

# RAG settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_SEARCH_RESULTS = 5

# Session settings
SESSION_TIMEOUT_HOURS = 24