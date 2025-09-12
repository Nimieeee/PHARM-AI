import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}
