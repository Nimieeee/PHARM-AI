"""
Clean OpenAI-compatible API client for PharmGPT
Simple, reliable chat completions with Groq and OpenRouter
"""

import openai
from groq import Groq
import os
import logging
import time
import re
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
    """Get API keys from Streamlit secrets or environment variables (fallback)."""
    import streamlit as st
    
    # Try Streamlit secrets first, fallback to environment variables
    try:
        groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY", os.environ.get("OPENROUTER_API_KEY"))
        mistral_key = st.secrets.get("MISTRAL_API_KEY", os.environ.get("MISTRAL_API_KEY"))
    except Exception:
        # Fallback to environment variables if secrets not available
        groq_key = os.environ.get("GROQ_API_KEY")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        mistral_key = os.environ.get("MISTRAL_API_KEY")
    
    return groq_key, openrouter_key, mistral_key

def get_model_configs():
    """Get model configurations with API keys - optimized for speed."""
    groq_key, openrouter_key, mistral_key = get_api_keys()
    
    return {
        "turbo": {
            "model": "llama-3.1-70b-versatile",
            "api_key": groq_key,
            "base_url": "https://api.groq.com/openai/v1",
            "description": "Llama 3.1 70B (Ultra Fast)",
            "use_native_groq": False,
            "max_tokens": 4096,
            "temperature": 0.3
        },
        "normal": {
            "model": "llama-3.1-8b-instant",
            "api_key": groq_key,
            "base_url": "https://api.groq.com/openai/v1",
            "description": "Llama 3.1 8B Instant (Lightning Fast)",
            "use_native_groq": False,
            "max_tokens": 4096,
            "temperature": 0.3
        },
        "premium": {
            "model": "mistral-large-latest",
            "api_key": mistral_key,
            "base_url": "https://api.mistral.ai/v1", 
            "description": "Mistral Large (High Quality)",
            "use_native_groq": False,
            "max_tokens": 4096,
            "temperature": 0.3
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
    """Get optimized max_tokens for speed."""
    # Reduced tokens for faster generation
    if "8b-instant" in model:
        return 2048  # Very fast responses
    elif "70b" in model:
        return 3072  # Fast but comprehensive
    else:
        return 4096  # Standard

def _get_client_for_model(model: str):
    """Get appropriate client for specific model (OpenAI or native Groq)."""
    model_configs = get_model_configs()
    
    for mode, config in model_configs.items():
        if config["model"] == model:
            if not config["api_key"]:
                raise ValueError(f"API key not configured for {mode} mode")
            
            # Use native Groq client for models that support advanced features
            if config.get("use_native_groq", False):
                return Groq(api_key=config["api_key"])
            else:
                return openai.OpenAI(
                    api_key=config["api_key"],
                    base_url=config["base_url"]
                )
    
    raise ValueError(f"Unknown model: {model}")

def chat_completion_fast(model: str, messages: List[Dict]) -> str:
    """Ultra-fast non-streaming completion for maximum speed."""
    try:
        client = _get_client_for_model(model)
        model_configs = get_model_configs()
        
        # Find model config
        model_config = None
        for mode, config in model_configs.items():
            if config["model"] == model:
                model_config = config
                break
        
        if not model_config:
            raise ValueError(f"Model config not found for: {model}")
        
        # Fast completion without streaming
        max_tokens = get_optimal_max_tokens(model, model_config["base_url"])
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=model_config.get("temperature", 0.3),
            max_tokens=max_tokens,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stream=False  # No streaming for maximum speed
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in fast completion: {e}")
        return f"Error generating response: {str(e)}"

def chat_completion_stream(model: str, messages: List[Dict]) -> Iterator[str]:
    """Generate ultra-fluid streaming chat completion with advanced features."""
    try:
        client = _get_client_for_model(model)
        model_configs = get_model_configs()
        
        # Find model config
        model_config = None
        for mode, config in model_configs.items():
            if config["model"] == model:
                model_config = config
                break
        
        if not model_config:
            raise ValueError(f"Model config not found for: {model}")
        
        # Use native Groq client with advanced features for supported models
        if model_config.get("use_native_groq", False):
            logger.info(f"Starting advanced Groq stream with reasoning and tools for model: {model}")
            
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5,
                max_completion_tokens=65536,
                top_p=1,
                reasoning_effort="medium",
                stream=True,
                stop=None,
                tools=[{"type": "browser_search"}]
            )
        else:
            # Optimized streaming for speed
            max_tokens = get_optimal_max_tokens(model, model_config["base_url"])
            logger.info(f"Starting optimized stream with {max_tokens} tokens for model: {model}")
            
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=model_config.get("temperature", 0.3),  # Lower temp for faster, focused responses
                max_tokens=max_tokens,
                top_p=0.9,  # Slightly more focused
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
        
        # Ultra-fast streaming with minimal buffering
        buffer = ""
        word_count = 0
        last_yield_time = time.time()
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                buffer += content
                
                # Optimized yield conditions for maximum speed:
                current_time = time.time()
                time_since_last_yield = current_time - last_yield_time
                
                # Yield more aggressively for speed
                should_yield = (
                    len(buffer) >= 8 or  # Smaller chunks for faster display
                    time_since_last_yield >= 0.08 or  # Faster max delay (80ms)
                    any(punct in buffer for punct in ['. ', '! ', '? ', '\n']) or  # Sentence breaks
                    ' ' in buffer and len(buffer) >= 4  # Word boundaries
                )
                
                if should_yield and buffer.strip():
                    yield buffer
                    buffer = ""
                    word_count += len(re.findall(r'\S+', buffer))
                    last_yield_time = current_time
                    
                    # No artificial delays - maximum speed
            
            # Silent finish reason handling (no user-visible messages)
            if chunk.choices[0].finish_reason is not None:
                # Yield any remaining buffer content
                if buffer.strip():
                    yield buffer
                
                finish_reason = chunk.choices[0].finish_reason
                logger.info(f"Stream completed: {finish_reason} (total words: ~{word_count})")
                
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        yield f"Error: {str(e)}"

def chat_completion(model: str, messages: List[Dict]) -> str:
    """Generate non-streaming chat completion with advanced features."""
    try:
        client = _get_client_for_model(model)
        model_configs = get_model_configs()
        
        # Find model config
        model_config = None
        for mode, config in model_configs.items():
            if config["model"] == model:
                model_config = config
                break
        
        if not model_config:
            raise ValueError(f"Model config not found for: {model}")
        
        # Use native Groq client with advanced features for supported models
        if model_config.get("use_native_groq", False):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5,
                max_completion_tokens=65536,
                top_p=1,
                reasoning_effort="medium",
                stream=False,
                stop=None,
                tools=[{"type": "browser_search"}]
            )
        else:
            # Standard OpenAI-compatible completion
            max_tokens = 7500
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5,
                max_tokens=max_tokens,
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
            temperature=0.5,
            max_tokens=10
        )
        
        return True
        
    except Exception as e:
        logger.error(f"API connection test failed for {model}: {e}")
        return False