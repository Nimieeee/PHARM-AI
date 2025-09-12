"""
Configuration settings for PharmBot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
APP_TITLE = "PharmBot - AI Pharmacology Assistant"
APP_ICON = "💊"

# File upload settings
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ['pdf', 'txt', 'csv', 'docx', 'doc', 'png', 'jpg', 'jpeg']

# User data settings
USER_DATA_DIR = "user_data"
UPLOAD_LIMIT_PER_DAY = -1  # -1 means unlimited uploads

# RAG settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_SEARCH_RESULTS = 5

# Session settings
SESSION_TIMEOUT_HOURS = 24