"""
Configuration settings for PharmGPT
"""

import streamlit as st
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue with system env vars

# API Configuration - Lazy loading to avoid secrets access outside Streamlit
def get_api_keys():
    """Get API keys from Streamlit secrets or environment variables."""
    try:
        # Try Streamlit secrets first (when in Streamlit context)
        if hasattr(st, 'secrets'):
            return st.secrets.get("GROQ_API_KEY"), st.secrets.get("OPENROUTER_API_KEY")
    except:
        pass
    
    # Fallback to environment variables
    return os.environ.get("GROQ_API_KEY"), os.environ.get("OPENROUTER_API_KEY")

# Initialize as None, will be loaded when needed
GROQ_API_KEY = None
OPENROUTER_API_KEY = None

# Model configurations - will be populated when API keys are loaded
def get_model_configs():
    """Get model configurations with API keys."""
    groq_key, openrouter_key = get_api_keys()
    
    return {
        "normal": {
            "model": "gemma2-9b-it",
            "api_key": groq_key,
            "base_url": "https://api.groq.com/openai/v1",
            "description": "Gemma2 9B Instruct (Balanced)"
        },
        "turbo": {
            "model": "openrouter/sonoma-sky-alpha",
            "api_key": openrouter_key,
            "base_url": "https://openrouter.ai/api/v1",
            "description": "Sonoma Sky Alpha (Fast)"
        }
    }

# Backward compatibility
MODEL_CONFIGS = {}

# Application settings
APP_TITLE = "PharmGPT - AI Pharmacology Assistant"
APP_ICON = "💊"

# File upload settings
MAX_FILE_SIZE_MB = 20
ALLOWED_FILE_TYPES = ['pdf', 'txt', 'csv', 'docx', 'doc', 'png', 'jpg', 'jpeg']

# Database settings - Supabase only
USE_SUPABASE = True  # Always use Supabase (file-based storage removed)

# Supabase configuration - Lazy loading
def get_supabase_config():
    """Get Supabase configuration from secrets or environment."""
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets'):
            return st.secrets.get("SUPABASE_URL"), st.secrets.get("SUPABASE_ANON_KEY")
    except:
        pass
    
    # Fallback to environment variables
    return os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")

# Initialize as None, will be loaded when needed
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