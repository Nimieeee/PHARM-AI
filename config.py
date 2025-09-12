import os
from pathlib import Path

# Try to load from environment first
API_KEY = os.getenv("GROQ_API_KEY")

# If not found, read directly from .env file
if not API_KEY:
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GROQ_API_KEY=') and not line.startswith('#'):
                    API_KEY = line.split('=', 1)[1].strip()
                    break

BASE_URL = "https://api.groq.com/openai/v1"



# Validate API key
if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found in environment variables. "
        "Please create a .env file with your Groq API key. "
        "Get one from: https://console.groq.com/keys"
    )

if not API_KEY.startswith("gsk_"):
    raise ValueError(
        f"Invalid Groq API key format. Found: '{API_KEY[:10]}...' "
        "API key should start with 'gsk_'. "
        "Get a valid key from: https://console.groq.com/keys"
    )

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}
