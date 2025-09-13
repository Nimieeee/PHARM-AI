"""
OpenAI-compatible API client for chat completions
Supports both Groq and OpenRouter APIs with performance optimizations
"""

import openai
from typing import Iterator, Dict, List
import streamlit as st
from config import get_model_configs
import hashlib
import json

def get_available_model_modes() -> Dict:
    """Get available model modes based on API key availability."""
    available_modes = {}
    model_configs = get_model_configs()
    
    for mode, config in model_configs.items():
        if config["api_key"]:
            available_modes[mode] = config
    
    return available_modes

@st.cache_resource
def get_client_for_model(model: str) -> openai.OpenAI:
    """Get OpenAI client for specific model - cached for performance."""
    # Find which config this model belongs to
    model_configs = get_model_configs()
    for mode, config in model_configs.items():
        if config["model"] == model:
            if not config["api_key"]:
                raise ValueError(f"API key not configured for {mode} mode")
            
            return openai.OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
    
    raise ValueError(f"Unknown model: {model}")

def _get_messages_hash(messages: List[Dict]) -> str:
    """Generate hash for message list to enable caching."""
    # Create a stable hash of the messages
    messages_str = json.dumps(messages, sort_keys=True)
    return hashlib.md5(messages_str.encode()).hexdigest()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def _cached_chat_completion(model: str, messages_hash: str, messages: List[Dict]) -> str:
    """Cached chat completion for identical requests."""
    try:
        client = get_client_for_model(model)
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)}"

def chat_completion_stream(model: str, messages: List[Dict]) -> Iterator[str]:
    """
    Generate streaming chat completion.
    
    Args:
        model: Model name to use
        messages: List of message dictionaries
        
    Yields:
        str: Chunks of the response
    """
    try:
        client = get_client_for_model(model)
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        st.error(f"Streaming error: {str(e)}")
        yield f"Error: {str(e)}"

def chat_completion(model: str, messages: List[Dict]) -> str:
    """
    Generate non-streaming chat completion with caching.
    
    Args:
        model: Model name to use
        messages: List of message dictionaries
        
    Returns:
        str: Complete response
    """
    # Use cached version for identical requests
    messages_hash = _get_messages_hash(messages)
    return _cached_chat_completion(model, messages_hash, messages)

def test_api_connection(model: str) -> bool:
    """Test API connection for a specific model."""
    try:
        client = get_client_for_model(model)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        return True
        
    except Exception:
        return False