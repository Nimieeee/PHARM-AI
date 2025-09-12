from openai import OpenAI
from config import API_KEY, BASE_URL

# Initialize OpenAI client
openai = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

def chat_completion(model: str, messages: list):
    """Get a standard chat completion response."""
    response = openai.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
