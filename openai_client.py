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

def chat_completion_stream(model: str, messages: list):
    """Get a streaming chat completion response."""
    stream = openai.chat.completions.create(
        model=model, 
        messages=messages,
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
