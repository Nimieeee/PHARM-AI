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

def get_available_model_modes() -> Dict:
    """Get available model modes based on API key availability."""
    available_modes = {}
    model_configs = get_model_configs()
    
    for mode, config in model_configs.items():
        if config["api_key"]:
            available_modes[mode] = config
    
    return available_modes

def get_model_token_limits() -> Dict:
    """Get unified token limits for all models."""
    return {
        "unified": {
            "max_tokens": 7500,
            "context_window": 128000,
            "description": "Unified high-capacity output for all models"
        }
    }

def get_optimal_max_tokens(model: str, base_url: str) -> int:
    """Get unified max_tokens for all models (7500 tokens)."""
    return 7500  # Unified limit for both Normal and Turbo modes

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
    """Generate ultra-fluid streaming chat completion with 7500 token capacity."""
    try:
        client = _get_client_for_model(model)
        
        # Unified 7500 token limit for all models
        max_tokens = 7500
        
        logger.info(f"Starting ultra-fluid stream with {max_tokens} tokens for model: {model}")
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=max_tokens,
            # Optimized parameters for fluid streaming
            top_p=0.95,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        # Ultra-fluid streaming - yield every chunk immediately
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
            
            # Silent finish reason handling (no user-visible messages)
            if chunk.choices[0].finish_reason is not None:
                finish_reason = chunk.choices[0].finish_reason
                logger.info(f"Stream completed: {finish_reason}")
                # No additional messages to maintain fluid experience
                
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        yield f"Error: {str(e)}"

def chat_completion(model: str, messages: List[Dict]) -> str:
    """Generate non-streaming chat completion with unified 7500 token capacity."""
    try:
        client = _get_client_for_model(model)
        
        # Unified 7500 token limit for all models
        max_tokens = 7500
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens,
            # Optimized parameters
            top_p=0.95,
            frequency_penalty=0.0,
            presence_penalty=0.0
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