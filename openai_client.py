"""
Clean OpenAI-compatible API client for PharmGPT
Simple, reliable chat completions with Groq and OpenRouter
"""

import openai
import os
import logging
from typing import Iterator, Dict, List

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_api_keys():
    """Get API keys from environment variables."""
    groq_key = os.environ.get("GROQ_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    return groq_key, openrouter_key

def get_model_configs():
    """Get model configurations with API keys."""
    groq_key, openrouter_key = get_api_keys()
    
    return {
        "normal": {
            "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
            "api_key": groq_key,
            "base_url": "https://api.groq.com/openai/v1",
            "description": "Llama 4 Maverick (Balanced)"
        },
        "turbo": {
            "model": "openrouter/sonoma-sky-alpha",
            "api_key": openrouter_key,
            "base_url": "https://openrouter.ai/api/v1",
            "description": "Sonoma Sky Alpha (Fast)"
        }
    }

def get_available_model_modes() -> Dict:
    """Get available model modes based on API key availability."""
    available_modes = {}
    model_configs = get_model_configs()
    
    for mode, config in model_configs.items():
        if config["api_key"]:
            available_modes[mode] = config
    
    return available_modes

def _get_client_for_model(model: str) -> openai.OpenAI:
    """Get OpenAI client for specific model."""
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

def chat_completion_stream(model: str, messages: List[Dict]) -> Iterator[str]:
    """Generate streaming chat completion."""
    try:
        client = _get_client_for_model(model)
        
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
        logger.error(f"Streaming error: {str(e)}")
        yield f"Error: {str(e)}"

def chat_completion(model: str, messages: List[Dict]) -> str:
    """Generate non-streaming chat completion."""
    try:
        client = _get_client_for_model(model)
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Chat completion error: {str(e)}")
        return f"Error: {str(e)}"

def test_api_connection(model: str) -> bool:
    """Test API connection for a specific model."""
    try:
        client = _get_client_for_model(model)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        return True
        
    except Exception as e:
        logger.error(f"API connection test failed for {model}: {e}")
        return False